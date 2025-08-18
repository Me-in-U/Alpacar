import gymnasium as gym
import highway_env
import numpy as np
from stable_baselines3 import SAC
from stable_baselines3.her.her_replay_buffer import HerReplayBuffer

# 환경 생성
env = gym.make(
    'custom-parking-v0',
    render_mode=None,
    config={
        "vehicles_count": 8,
        "duration": 500,
        "vehicle_heading_offset": np.deg2rad(10),
        "vehicle_diversity": True,
        "test_vehicle_diversity": True,
        "controller_mode": "random"
    }
)

# HER 리플레이 버퍼 설정
her_kwargs = dict(
    n_sampled_goal=4,
    goal_selection_strategy='future'
)

# 기존 모델 로드 (HER 버퍼 포함)
model = SAC.load(
    "sac_highway_v2",
    env=env,
    replay_buffer_class=HerReplayBuffer,
    replay_buffer_kwargs=her_kwargs,
)

# 학습 진행
model.learn(
    total_timesteps=500_000,
    progress_bar=True,
)

# 모델 저장
model.save("sac_highway_v2")
