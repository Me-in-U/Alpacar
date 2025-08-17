from __future__ import annotations

from abc import abstractmethod

import numpy as np
from gymnasium import Env

from highway_env.envs.common.abstract import AbstractEnv
from highway_env.envs.common.observation import (
    MultiAgentObservation,
    observation_factory,
)
from highway_env.road.lane import LineType, StraightLane
from highway_env.road.road import Road, RoadNetwork
from highway_env.vehicle.graphics import VehicleGraphics
from highway_env.vehicle.kinematics import Vehicle, SmallVehicle, MediumVehicle
from highway_env.vehicle.objects import Landmark, Obstacle


class GoalEnv(Env):
    """
    목표 기반 환경을 위한 인터페이스.

    이 인터페이스는 Stable Baseline3의 Hindsight Experience Replay (HER) 에이전트와 같은 에이전트에 필요합니다.
    원래는 https://github.com/openai/gym의 일부였지만, 나중에
    https://github.com/Farama-Foundation/gym-robotics로 이동했습니다. 이 프로젝트의 의존성에 gym-robotics를 추가할 수 없습니다.
    공식 PyPi 패키지가 없고, PyPi는 git 저장소에 대한 직접 의존성을 허용하지 않기 때문입니다.
    대신, 여기서 인터페이스를 재현합니다.

    목표 기반 환경입니다. 일반적인 OpenAI Gym 환경과 동일하게 작동하지만
    observation_space에 필요한 구조를 부과합니다. 더 구체적으로, observation
    space는 최소한 세 가지 요소, 즉 `observation`, `desired_goal`, `achieved_goal`을 포함해야 합니다.
    여기서 `desired_goal`은 에이전트가 달성하려고 시도해야 하는 목표를 지정합니다.
    `achieved_goal`은 대신 현재 달성한 목표입니다. `observation`은 평소와 같이
    환경의 실제 관찰을 포함합니다.
    """

    @abstractmethod
    def compute_reward(
        self, achieved_goal: np.ndarray, desired_goal: np.ndarray, info: dict
    ) -> float:
        """스텝 보상을 계산합니다. 이는 보상 함수를 외부화하고
        원하는 목표와 달성된 목표에 의존하게 만듭니다. 목표와 독립적인 추가 보상을 포함하려면
        'info'에 필요한 값을 포함하고 그에 따라 계산할 수 있습니다.
        Args:
            achieved_goal (object): 실행 중에 달성된 목표
            desired_goal (object): 에이전트가 달성하려고 시도하도록 요청한 원하는 목표
            info (dict): 추가 정보가 포함된 정보 딕셔너리
        Returns:
            float: 제공된 달성된 목표에 해당하는 보상 (원하는 목표에 대해).
            다음이 항상 참이어야 함을 참고하세요:
                ob, reward, done, info = env.step()
                assert reward == env.compute_reward(ob['achieved_goal'], ob['desired_goal'], info)
        """
        raise NotImplementedError


class CustomParkingEnv(AbstractEnv, GoalEnv):
    """
    연속 제어 환경.

    에이전트가 위치와 속도를 관찰하고 가속도와 조향을 제어하여
    주어진 목표에 도달해야 하는 도달형 작업을 구현합니다.

    아이디어와 초기 구현에 대한 크레딧은 Munir Jojo-Verge에게 있습니다.
    """

    # GrayscaleObservation이 있는 주차 환경의 경우, 환경이
    # 보상과 정보를 계산하기 위해 이 PARKING_OBS가 필요합니다.
    # Mcfly(https://github.com/McflyWZX)에 의해 버그가 수정됨
    PARKING_OBS = {
        "observation": {
            "type": "KinematicsGoal",
            "features": ["x", "y", "vx", "vy", "cos_h", "sin_h"],
            "scales": [100, 100, 5, 5, 1, 1],
            "normalize": False,
        }
    }

    def __init__(self, config: dict = None, render_mode: str | None = None) -> None:
        super().__init__(config, render_mode)
        self.observation_type_parking = None

    @classmethod
    def default_config(cls) -> dict:
        config = super().default_config()
        config.update(
            {
                "observation": {
                    "type": "KinematicsGoal",
                    "features": ["x", "y", "vx", "vy", "cos_h", "sin_h"],
                    "scales": [100, 100, 5, 5, 1, 1],
                    "normalize": False,
                },
                "action": {
                    "type": "ContinuousAction",
                    "steering_range": [-np.deg2rad(45), np.deg2rad(45)]
                },
                "reward_weights": [1, 0.3, 0, 0, 0.02, 0.02],
                "success_goal_reward": 0.12,
                "collision_reward": -5,
                "simulation_frequency": 15,
                "policy_frequency": 5,
                "duration": 100,
                "screen_width": 600,
                "screen_height": 300,
                "centering_position": [0.5, 0.5],
                "scaling": 7,
                "controlled_vehicles": 1,
                "vehicles_count": 0,
                "add_walls": True,
                "vehicle_heading_offset": 0.0,  # 차량 방향 오프셋 범위 (라디안, 절대값)
                "random_vehicle_types": True,  # 랜덤 차량 타입 사용
                "vehicle_type_probabilities": [0.6, 0.3, 0.1],  # [Vehicle, SmallVehicle, MediumVehicle] 확률
            }
        )
        return config

    def define_spaces(self) -> None:
        """
        설정에서 관찰과 액션의 타입과 공간을 설정합니다.
        """
        super().define_spaces()
        self.observation_type_parking = observation_factory(
            self, self.PARKING_OBS["observation"]
        )

    def _info(self, obs, action) -> dict:
        info = super()._info(obs, action)
        if isinstance(self.observation_type, MultiAgentObservation):
            success = tuple(
                self._is_success(agent_obs["achieved_goal"], agent_obs["desired_goal"])
                for agent_obs in obs
            )
        else:
            obs = self.observation_type_parking.observe()
            success = self._is_success(obs["achieved_goal"], obs["desired_goal"])
        info.update({"is_success": success})
        return info

    def _reset(self):
        self._create_road()
        self._create_vehicles()

    def _create_road(self, spots: int = 6) -> None:
        """
        Create a road composed of straight adjacent lanes with wider spacing for parked vehicles.

        :param spots: number of spots in the parking
        """
        net = RoadNetwork()
        width = 4.0
        lt = (LineType.CONTINUOUS, LineType.CONTINUOUS)
        x_offset = 2.0  # lane 간격을 0에서 6.0으로 확장
        y_offset = 10
        length = 8
        x_shift = 16
        for k in range(spots):
            x = x_shift + (k + 1 - spots // 2) * (width + x_offset) - width / 2
            net.add_lane(
                "a",
                "b",
                StraightLane(
                    [x, y_offset], [x, y_offset + length], width=width, line_types=lt
                ),
            )
            net.add_lane(
                "b",
                "c",
                StraightLane(
                    [x, -y_offset], [x, -y_offset - length], width=width, line_types=lt
                ),
            )

        self.road = Road(
            network=net,
            np_random=self.np_random,
            record_history=self.config["show_trajectories"],
        )

    def _get_random_vehicle_class(self):
        """랜덤 차량 클래스 반환"""
        if not self.config["random_vehicle_types"]:
            return Vehicle
        
        vehicle_classes = [Vehicle, SmallVehicle, MediumVehicle]
        probabilities = self.config["vehicle_type_probabilities"]
        
        # 확률 정규화
        probabilities = np.array(probabilities)
        probabilities = probabilities / probabilities.sum()
        
        return self.np_random.choice(vehicle_classes, p=probabilities)

    def _create_vehicles(self) -> None:
        """Create some new random vehicles of a given type, and add them on the road."""
        empty_spots = list(self.road.network.lanes_dict().keys())

        # Controlled vehicles
        self.controlled_vehicles = []
        for i in range(self.config["controlled_vehicles"]):
            x0 = (i - self.config["controlled_vehicles"] // 2) * 9
            vehicle = self.action_type.vehicle_class(
                self.road, [x0, 0], 2 * np.pi * self.np_random.uniform(), 0
            )
            # 설정에서 방향 오프셋 적용
            vehicle.color = VehicleGraphics.EGO_COLOR
            self.road.vehicles.append(vehicle)
            self.controlled_vehicles.append(vehicle)
            empty_spots.remove(vehicle.lane_index)

        # Goal
        for vehicle in self.controlled_vehicles:
            lane_index = empty_spots[self.np_random.choice(np.arange(len(empty_spots)))]
            lane = self.road.network.get_lane(lane_index)
            vehicle.goal = Landmark(
                self.road, lane.position(lane.length / 2, 0), heading=lane.heading
            )
            self.road.objects.append(vehicle.goal)
            empty_spots.remove(lane_index)

        # Other vehicles
        for i in range(self.config["vehicles_count"]):
            if not empty_spots:
                continue
            lane_index = empty_spots[self.np_random.choice(np.arange(len(empty_spots)))]
            
            # 랜덤 차량 클래스 선택
            vehicle_class = self._get_random_vehicle_class()
            v = vehicle_class.make_on_lane(self.road, lane_index, 4, speed=0)
            
            # 설정에서 방향 오프셋 범위 내에서 랜덤 적용
            offset_range = self.config["vehicle_heading_offset"]
            if offset_range > 0:
                random_offset = self.np_random.uniform(-offset_range, offset_range)
                v.heading += random_offset
            self.road.vehicles.append(v)
            empty_spots.remove(lane_index)

        # Walls (테두리 벽들은 그대로 유지)
        if self.config["add_walls"]:
            width, height = 70, 42
            for y in [-height / 2, height / 2]:
                obstacle = Obstacle(self.road, [0, y])
                obstacle.LENGTH, obstacle.WIDTH = (width, 1)
                obstacle.diagonal = np.sqrt(obstacle.LENGTH**2 + obstacle.WIDTH**2)
                self.road.objects.append(obstacle)
            for x in [-width / 2, width / 2]:
                obstacle = Obstacle(self.road, [x, 0], heading=np.pi / 2)
                obstacle.LENGTH, obstacle.WIDTH = (height, 1)
                obstacle.diagonal = np.sqrt(obstacle.LENGTH**2 + obstacle.WIDTH**2)
                self.road.objects.append(obstacle)

        # 내부 장애물들을 주차된 차량으로 변경
        self._create_parked_vehicles()

    def _create_parked_vehicles(self):
        """내부 장애물들을 주차된 차량으로 생성"""
        
        # 기존 내부 장애물 위치들을 차량으로 대체
        parked_positions = [
            # 좌측 주차된 차량들
            ([i, -11], np.pi / 2) for i in range(-11, 0, 2)
        ] + [
            # 우측 주차된 차량들  
            ([i, 11], np.pi / 2) for i in range(-11, 0, 2)
        ] + [
            # 입구 근처 주차된 차량들
            ([18-1, -11], np.pi / 2),
            ([18-1, 11], np.pi / 2),
            ([30-1, -10.5], np.pi / 2),
            ([30-1, 10.5], np.pi / 2),
        ]
        
        for position, heading in parked_positions:
            # 주차된 차량 생성 (속도 0, 정지 상태)
            parked_vehicle = Vehicle(
                self.road, 
                position, 
                heading, 
                speed=0
            )
            # 주차된 차량의 크기 조정 (더 작게)
            parked_vehicle.LENGTH = 2.0  # 기본 4.0에서 2.0으로 축소
            parked_vehicle.WIDTH = 1.5   # 기본 2.0에서 1.5로 축소
            # 주차된 차량은 다른 색상으로 표시
            parked_vehicle.color = (0.7, 0.7, 0.7)  # 회색
            self.road.vehicles.append(parked_vehicle)

    def compute_reward(
        self,
        achieved_goal: np.ndarray,
        desired_goal: np.ndarray,
        info: dict,
        p: float = 0.5,
    ) -> float:
        """
        목표에 대한 근접도가 보상됩니다

        가중 p-노름을 사용합니다

        :param achieved_goal: 달성된 목표
        :param desired_goal: 원했던 목표
        :param dict info: 추가 정보
        :param p: 보상에 사용되는 Lp^p 노름. p<1을 사용하여 [0, 1]에서 높은 첨도를 가진 보상을 얻으세요
        :return: 해당하는 보상
        """
        return -np.power(
            np.dot(
                np.abs(achieved_goal - desired_goal),
                np.array(self.config["reward_weights"]),
            ),
            p,
        )

    def _reward(self, action: np.ndarray) -> float:
        obs = self.observation_type_parking.observe()
        obs = obs if isinstance(obs, tuple) else (obs,)
        reward = sum(
            self.compute_reward(
                agent_obs["achieved_goal"], agent_obs["desired_goal"], {}
            )
            for agent_obs in obs
        )
        reward += self.config["collision_reward"] * sum(
            v.crashed for v in self.controlled_vehicles
        )
        return reward

    def _is_success(self, achieved_goal: np.ndarray, desired_goal: np.ndarray) -> bool:
        return (
            self.compute_reward(achieved_goal, desired_goal, {})
            > -self.config["success_goal_reward"]
        )

    def _is_terminated(self) -> bool:
        """자기 차량이 충돌하거나 목표에 도달하거나 시간이 초과되면 에피소드가 종료됩니다."""
        crashed = any(vehicle.crashed for vehicle in self.controlled_vehicles)
        obs = self.observation_type_parking.observe()
        obs = obs if isinstance(obs, tuple) else (obs,)
        success = all(
            self._is_success(agent_obs["achieved_goal"], agent_obs["desired_goal"])
            for agent_obs in obs
        )
        return bool(crashed or success)

    def _is_truncated(self) -> bool:
        """시간이 초과되면 에피소드가 중단됩니다."""
        return self.time >= self.config["duration"]

    

    def extract_goal_features(self, vehicle: Vehicle):
        """
        vehicle: 주차 목표(goal)가 할당된 에이전트 차량 객체
        self: CustomParkingEnv 인스턴스
        반환값: dict (정형 데이터 row)
        """

        def parse_spot_num(lane_idx):
            if isinstance(lane_idx, str):
                return int(lane_idx.split('_')[-1])
            if isinstance(lane_idx, tuple):
                for item in lane_idx:
                    if isinstance(item, str) and '_' in item:
                        try:
                            return int(item.split('_')[-1])
                        except Exception:
                            continue
            raise ValueError(f"spot 번호 파싱 실패: {lane_idx}")

        def make_adjacent_idx(lane_idx, offset):
            if isinstance(lane_idx, tuple):
                result = []
                for item in lane_idx:
                    if isinstance(item, str) and '_' in item:
                        prefix, num = item.split('_')
                        try:
                            new_idx = int(num) + offset
                            result.append(f"{prefix}_{new_idx}")
                        except Exception:
                            result.append(item)
                    else:
                        result.append(item)
                return tuple(result)
            if isinstance(lane_idx, str):
                prefix, num = lane_idx.split('_')
                return f"{prefix}_{int(num)+offset}"
            return None
            
        # 1. 목표 Landmark로부터 goal_lane 및 인덱스 추출
        goal_landmark = vehicle.goal
        if goal_landmark is None:
            raise ValueError("vehicle.goal이 지정되지 않았습니다.")
        
        # lane 추출 (position 기준)
        lane_idx = None
        goal_lane = None
        for idx, lane in self.road.network.lanes_dict().items():
            if np.allclose(lane.position(lane.length/2, 0), goal_landmark.position, atol=0.1):
                lane_idx = idx
                goal_lane = lane
                break

        if lane_idx is None:
            raise ValueError("goal에 해당하는 lane을 찾을 수 없습니다.")

        goal_position = goal_lane.position(goal_lane.length/2, 0)
        goal_x = goal_position[0]
        
        left_lane = None
        right_lane = None
        
        # 에이전트의 현재 위치를 기준으로 진입 방향 판단
        agent_position = self.controlled_vehicles[0].position
        
        for idx, lane in self.road.network.lanes_dict().items():
            if idx == lane_idx:  # goal lane 자체는 제외
                continue
                
            lane_position = lane.position(lane.length/2, 0)
            lane_x = lane_position[0]
            lane_y = lane_position[1]
            goal_y = goal_position[1]
            
            # 같은 y축 영역에 있는 lane들 중에서
            if abs(lane_y - goal_y) < 2.0:
                # 에이전트 기준으로 goal까지의 벡터 계산
                to_goal = np.array([goal_x - agent_position[0], goal_y - agent_position[1]])
                to_lane = np.array([lane_x - agent_position[0], lane_y - agent_position[1]])
                
                # 에이전트에서 goal을 바라볼 때의 좌우 판단 (외적 사용)
                cross_product = np.cross(to_goal, to_lane)
                distance = np.linalg.norm(to_lane - to_goal)
                
                # 적절한 거리 내에 있으면서 좌우 판단
                if distance < 8.0:  # 적절한 거리 내
                    if cross_product > 0:  # 오른쪽 (에이전트 기준)
                        right_lane = lane
                    elif cross_product < 0:  # 왼쪽 (에이전트 기준)
                        left_lane = lane

        def find_vehicle_in_lane(lane):
            """lane에 주차된 차량 정보 반환 (에이전트 차량과 기둥 차량 제외), 없으면 None"""
            if lane is None:
                return None
            for v in self.road.vehicles:
                if v in self.controlled_vehicles:
                    continue
                
                if (v.speed == 0 and hasattr(v, 'color') and v.color == (0.7, 0.7, 0.7)):
                    continue
                
                s, lateral = lane.local_coordinates(v.position)
                
                if (0 <= s <= lane.length and 
                    abs(lateral) <= lane.width * 0.8):
                    return v
            return None

        def find_adjacent_pillar_vehicles(lane, side="left"):
            """lane의 바로 좌우에 있는 기둥 차량들만 찾기"""
            pillar_vehicles = []
            if lane is None:
                return pillar_vehicles
            
            lane_center = lane.position(lane.length/2, 0)
            lane_heading = lane.heading
            
            # lane의 좌우 방향 벡터 계산
            perp_vector = np.array([-np.sin(lane_heading), np.cos(lane_heading)])
            if side == "left":
                perp_vector = -perp_vector
            
            for v in self.road.vehicles:
                if v.speed == 0 and hasattr(v, 'color') and v.color == (0.7, 0.7, 0.7):
                    v_pos = np.array(v.position)
                    lane_pos = np.array(lane_center)
                    
                    to_vehicle = v_pos - lane_pos
                    
                    dot_product = np.dot(to_vehicle, perp_vector)
                    
                    x_dist = abs(to_vehicle[0])
                    y_dist = abs(to_vehicle[1])
                    
                    if (dot_product > 0 
                        and y_dist > lane.width/2 
                        and y_dist < lane.width/2 + 5.0 
                        and x_dist < 6.0):  
                        pillar_vehicles.append(v)
            
            return pillar_vehicles

        def get_vehicle_features(v, lane):
            """차량 객체 및 해당 lane에서 피처 추출"""
            if v is None or lane is None:
                return {
                    "occupied": 0,
                    "angle": 0.0,
                    "offset": 0.0,
                    "size": 0,  # 0: 소형, 1: 일반, 2: 대형
                    "width": 0.0,
                    "length": 0.0
                }
            angle = (v.heading - lane.heading)  # lane 기준 차량 각도
            offset = lane.local_coordinates(v.position)[1]
            # 차량 크기 분류: 0=소형, 1=일반, 2=대형
            if isinstance(v, SmallVehicle):
                size = 0
            elif isinstance(v, MediumVehicle):
                size = 2
            else:  # Vehicle (일반)
                size = 1
            width = getattr(v, "WIDTH", 0.0)
            length = getattr(v, "LENGTH", 0.0)
            return {
                "occupied": 1,
                "angle": angle,
                "offset": offset,
                "size": size,
                "width": width,
                "length": length
            }

        def get_pillar_features(pillar_vehicles, lane):
            """기둥 차량들의 통합 피처 추출"""
            if not pillar_vehicles or lane is None:
                return {
                    "pillar_count": 0,
                    "pillar_distance": 0.0,
                    "has_pillar": 0
                }
            
            # 가장 가까운 기둥 차량 찾기
            lane_center = lane.position(lane.length/2, 0)
            closest_pillar = min(pillar_vehicles, 
                               key=lambda v: np.linalg.norm(np.array(v.position) - np.array(lane_center)))
            
            distance = np.linalg.norm(np.array(closest_pillar.position) - np.array(lane_center))
            
            return {
                "pillar_count": len(pillar_vehicles),
                "pillar_distance": distance,
                "has_pillar": 1
            }

        # 좌우 차량 피처 추출
        left_v = find_vehicle_in_lane(left_lane)
        right_v = find_vehicle_in_lane(right_lane)
        left_feats = get_vehicle_features(left_v, left_lane)
        right_feats = get_vehicle_features(right_v, right_lane)

        # goal lane의 바로 좌우에 있는 기둥 차량들만 찾기
        left_pillars = find_adjacent_pillar_vehicles(goal_lane, side="left")
        right_pillars = find_adjacent_pillar_vehicles(goal_lane, side="right")
        
        # 기둥 피처 추출 (goal_lane 기준으로)
        left_pillar_feats = get_pillar_features(left_pillars, goal_lane)
        right_pillar_feats = get_pillar_features(right_pillars, goal_lane)

        return {
            "left_occupied": left_feats["occupied"],
            "left_angle": left_feats["angle"],
            "left_offset": left_feats["offset"],
            "left_size": left_feats["size"],
            "left_width": left_feats["width"],
            "left_length": left_feats["length"],
            "right_occupied": right_feats["occupied"],
            "right_angle": right_feats["angle"],
            "right_offset": right_feats["offset"],
            "right_size": right_feats["size"],
            "right_width": right_feats["width"],
            "right_length": right_feats["length"],
            "left_has_pillar": left_pillar_feats["has_pillar"],
            "right_has_pillar": right_pillar_feats["has_pillar"],
        }




class ParkingEnvActionRepeat(CustomParkingEnv):
    def __init__(self):
        super().__init__({"policy_frequency": 1, "duration": 20})


class ParkingEnvParkedVehicles(CustomParkingEnv):
    def __init__(self):
        super().__init__({"vehicles_count": 10})
