import subprocess
import os
from datetime import datetime

# --- 설정 ---
REPO_URL = "https://github.com/KimJinHyuk1984/todrlqn.git"
BRANCH = "main"
# --- 설정 끝 ---

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

def run_git_command(command, capture=False, ignore_errors=False):
    """Git 명령어를 실행하고 결과를 처리합니다."""
    print(f"👉 실행: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=not ignore_errors,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        # stderr에 내용이 있고, 특정 성공 메시지가 아닌 경우 출력
        if result.stderr and "no local changes to save" not in result.stderr.lower():
            print(f"   (참고: {result.stderr.strip()})")

        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 명령어 오류 발생: {' '.join(command)}")
        if e.stderr:
            print(f"오류 내용: {e.stderr.strip()}")
        if e.stdout:
            print(f"출력 내용: {e.stdout.strip()}")
        exit(1)
    except FileNotFoundError:
        print("❌ 'git' 명령어를 찾을 수 없습니다. Git이 설치되어 있는지 확인하세요.")
        exit(1)

# 1. Git 저장소 확인 및 초기화
if not os.path.exists(os.path.join(current_dir, ".git")):
    print("🧱 Git 저장소가 없네요. 초기화 및 원격과 동기화를 시작합니다...")
    run_git_command(["git", "init"])
    run_git_command(["git", "remote", "add", "origin", REPO_URL])
    
    # 원격 브랜치가 존재하는지 확인
    remote_check_result = run_git_command(["git", "ls-remote", "--heads", REPO_URL, BRANCH], capture=True, ignore_errors=True)
    if remote_check_result.stdout:
        print("   원격 저장소에 브랜치가 존재하여 동기화를 진행합니다.")
        run_git_command(["git", "fetch", "origin"])
        run_git_command(["git", "reset", "--hard", f"origin/{BRANCH}"])
        run_git_command(["git", "branch", f"--set-upstream-to=origin/{BRANCH}", BRANCH])
    else:
        print("   원격 저장소가 비어있거나 브랜치가 없습니다. 초기 커밋을 진행합니다.")

# --- 변경된 작업 순서 ---

# 2. 변경사항 추가 (Add)
print("\n➕ 변경된 모든 파일을 추가합니다...")
run_git_command(["git", "add", "."])

# 3. 커밋 (Commit)
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
commit_msg = f"자동 업데이트: {now}"
print(f"\n💬 로컬 변경사항을 먼저 커밋합니다: '{commit_msg}'")

# 커밋은 실패할 수 있으므로(변경사항 없음) 오류 무시 후 결과 확인
result = run_git_command(["git", "commit", "-m", commit_msg], capture=True, ignore_errors=True)

# 커밋할 내용이 있는지 확인
if "nothing to commit" in result.stdout.lower() or (result.stderr and "nothing to commit" in result.stderr.lower()):
    print("📁 새로운 로컬 변경사항이 없습니다. 원격 변경사항만 확인합니다.")
    # 커밋할 게 없어도 pull은 해야 함
else:
    print("✅ 로컬 변경사항 커밋 완료!")

# 4. 원격 저장소의 최신 변경사항 가져오고 재배치 (Pull with Rebase)
print("\n🔄 원격 저장소의 최신 변경사항을 가져와 로컬 커밋 위에 재배치합니다...")
try:
    run_git_command(["git", "pull", "origin", BRANCH, "--rebase"])
except subprocess.CalledProcessError:
    print("❌ Pull/Rebase 실패! 충돌이 발생했을 수 있습니다. 수동으로 해결해주세요.")
    print("💡 해결 팁: 'git status'로 확인 후 충돌 파일을 수정하고 'git add [파일명]', 'git rebase --continue'를 실행하세요.")
    exit(1)

# 5. 최종 결과 푸시 (Push)
print("\n🚀 최종 결과를 원격 저장소에 업로드합니다...")
run_git_command(["git", "push", "origin", BRANCH])
print("\n🎉 모든 작업이 성공적으로 완료되었습니다!")