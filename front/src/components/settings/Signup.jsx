import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export const SignUpPage = () => {
  const navigate = useNavigate();

  // 입력값 및 에러 메시지 상태
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  // 아이디 중복 확인 결과 (null: 확인하지 않음, true: 사용 가능, false: 중복)
  const [isUsernameAvailable, setIsUsernameAvailable] = useState(null);

  // 아이디 중복 체크 함수 (Django API 호출)
  const handleCheckUsername = async () => {
    if (!username) {
      setErrorMessage("아이디를 입력하세요.");
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/api/users/check_username/?username=${encodeURIComponent(
          username
        )}`
      );
      if (!response.ok) {
        setErrorMessage("중복 확인에 실패했습니다.");
        return;
      }
      const data = await response.json();
      if (data.exists) {
        setErrorMessage("이미 사용 중인 아이디입니다.");
        setIsUsernameAvailable(false);
      } else {
        setErrorMessage("사용 가능한 아이디입니다.");
        setIsUsernameAvailable(true);
      }
    } catch (error) {
      console.error(error);
      setErrorMessage("중복 확인 중 오류가 발생했습니다.");
    }
  };

  // 회원가입 처리 함수 (Django API 호출)
  const handleSignUp = async (e) => {
    e.preventDefault();

    // 아이디 중복 체크가 통과되지 않은 경우 막기
    if (isUsernameAvailable !== true) {
      setErrorMessage("아이디 중복 확인을 진행해주세요.");
      return;
    }

    try {
      const response = await fetch(
        "http://localhost:8000/api/users/register/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ username, password }),
        }
      );
      if (!response.ok) {
        const data = await response.json();
        setErrorMessage(data.error || "회원가입에 실패했습니다.");
        return;
      }
      // 회원가입 성공 시 입력값 초기화 및 로그인 페이지로 이동
      setUsername("");
      setPassword("");
      setErrorMessage("");
      navigate("/login");
    } catch (error) {
      console.error(error);
      setErrorMessage("회원가입 중 오류가 발생했습니다.");
    }
  };

  return (
    <div className="bg-white p-4 rounded-3 shadow-sm">
      <h3 className="mb-4">회원가입</h3>
      {errorMessage && <div className="alert alert-danger">{errorMessage}</div>}
      <form onSubmit={handleSignUp}>
        <div className="mb-3 d-flex">
          <div className="flex-grow-1 me-2">
            <label htmlFor="username" className="form-label">
              아이디
            </label>
            <input
              type="text"
              className="form-control"
              id="username"
              placeholder="아이디를 입력하세요"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
                // 아이디가 변경되면 이전 중복 체크 결과 초기화
                setIsUsernameAvailable(null);
              }}
              required
            />
          </div>
          <div className="d-flex align-items-end">
            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={handleCheckUsername}
            >
              중복 확인
            </button>
          </div>
        </div>
        <div className="mb-3">
          <label htmlFor="password" className="form-label">
            비밀번호
          </label>
          <input
            type="password"
            className="form-control"
            id="password"
            placeholder="비밀번호를 입력하세요"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="btn btn-primary">
          회원가입
        </button>
      </form>
    </div>
  );
};
