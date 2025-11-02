// 비밀번호 표시/숨김 + 제출 시 불일치 처리
document.addEventListener('DOMContentLoaded', () => {
  const form   = document.getElementById('signupForm');
  const pw1    = document.getElementById('password');
  const pw2    = document.getElementById('confirm_password');
  const toggle = document.getElementById('togglePw');
  const errEl  = document.getElementById('pw_error');

  if (!form || !pw1 || !pw2 || !toggle || !errEl) return; // 안전장치

  //임시
  // 비밀번호 표시 토글
  function setType(show) {
    const t = show ? 'text' : 'password';
    pw1.type = t;
    pw2.type = t;
  }
  setType(toggle.checked);
  toggle.addEventListener('change', () => setType(toggle.checked));

  // 제출 시: 불일치면 제출 중단 + 재확인 비우고 포커스 + 오류 문구 표시
  form.addEventListener('submit', (e) => {
    if (pw1.value !== pw2.value) {
      e.preventDefault();
      pw2.value = '';
      pw2.focus();
      errEl.style.display = 'block';
      return false;
    }
  });

  // 입력 중 일치하면 오류 문구 숨기기
  function maybeHideError() {
    if (pw1.value && pw2.value && pw1.value === pw2.value) {
      errEl.style.display = 'none';
    }
  }
  pw1.addEventListener('input', maybeHideError);
  pw2.addEventListener('input', maybeHideError);
});
