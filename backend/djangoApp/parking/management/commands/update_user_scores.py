# parking/management/commands/update_user_scores.py
from django.core.management.base import BaseCommand
from django.db.models import Count
from accounts.models import User
from parking.models import update_user_average_score


class Command(BaseCommand):
    help = '모든 사용자의 평균 주차 점수를 재계산하여 업데이트합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='특정 사용자 ID의 점수만 업데이트 (생략시 모든 사용자)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='상세한 업데이트 정보를 출력합니다.',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        verbose = options.get('verbose')

        if user_id:
            # 특정 사용자만 업데이트
            try:
                user = User.objects.get(id=user_id)
                old_score = user.score
                update_user_average_score(user)
                user.refresh_from_db()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'사용자 {user.nickname}({user_id})의 점수가 {old_score} → {user.score}로 업데이트되었습니다.'
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'사용자 ID {user_id}를 찾을 수 없습니다.')
                )
        else:
            # 모든 사용자 업데이트
            users_with_history = User.objects.filter(
                score_histories__isnull=False
            ).distinct().annotate(
                history_count=Count('score_histories')
            )
            
            updated_count = 0
            
            for user in users_with_history:
                old_score = user.score
                update_user_average_score(user)
                user.refresh_from_db()
                updated_count += 1
                
                if verbose:
                    self.stdout.write(
                        f'사용자 {user.nickname}: {old_score} → {user.score} '
                        f'(총 {user.history_count}개 기록)'
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'총 {updated_count}명의 사용자 점수가 업데이트되었습니다.'
                )
            )
            
            if verbose:
                # 통계 정보 출력
                total_users = User.objects.count()
                users_without_history = total_users - updated_count
                
                self.stdout.write('\n=== 업데이트 통계 ===')
                self.stdout.write(f'전체 사용자: {total_users}명')
                self.stdout.write(f'점수 히스토리가 있는 사용자: {updated_count}명')
                self.stdout.write(f'점수 히스토리가 없는 사용자: {users_without_history}명')