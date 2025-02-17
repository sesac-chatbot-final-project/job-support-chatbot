import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";

export const SignUpPage = () => {
  const navigate = useNavigate();
  const mainColor = "#5e6aec";

  // 입력값 및 에러 메시지 상태
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isUsernameAvailable, setIsUsernameAvailable] = useState(null);

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

  const handleSignUp = async (e) => {
    e.preventDefault();
    if (isUsernameAvailable !== true) {
      setErrorMessage("아이디 중복 확인을 진행해주세요.");
      return;
    }

    try {
      const response = await fetch(
        "http://localhost:8000/api/users/register/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        }
      );
      if (!response.ok) {
        const data = await response.json();
        setErrorMessage(data.error || "회원가입에 실패했습니다.");
        return;
      }
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
    <div
      className="d-flex flex-column min-vh-100"
      style={{ width: "100vw", maxWidth: "none" }}
    >
      {/* Header */}
      <header
        className="d-flex justify-content-between align-items-center px-4 py-3 container-fluid px-0"
        style={{ backgroundColor: mainColor }}
      >
        <div
          className="container d-flex justify-content-between align-items-center"
          style={{ maxWidth: "1200px" }}
        >
          <img
            src="/images/logo.png"
            alt="Logo"
            className="h-50 cursor-pointer"
            onClick={() => navigate("/")}
          />
          <button
            onClick={() => navigate("/")}
            className="btn btn-outline-light rounded-4"
          >
            홈으로
          </button>
        </div>
      </header>
      <div
        className="bg-white p-5 rounded-5 shadow-lg text-center "
        style={{
          width: "500px",
          margin: "0 auto",
          marginTop: "50px",
          fontFamily: "Nanum Gothic",
        }}
      >
        <h3 className="mb-4 text-center" style={{ color: "GrayText" }}>
          <strong>회원가입</strong>
        </h3>
        {errorMessage && (
          <div className="alert alert-danger">{errorMessage}</div>
        )}
        <form onSubmit={handleSignUp}>
          <div className="mb-3 text-start px-2 fw-bold">
            <label
              htmlFor="username"
              className="form-label"
              style={{ color: "GrayText" }}
            >
              아이디
            </label>
            <div className="input-group">
              <input
                type="text"
                className="form-control rounded-4 "
                id="username"
                placeholder="아이디를 입력하세요"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  setIsUsernameAvailable(null);
                }}
                required
              />
              <button
                type="button"
                className="btn btn-outline-secondary rounded-5 ms-2"
                onClick={handleCheckUsername}
              >
                중복 확인
              </button>
            </div>
          </div>
          <div className="mb-3 text-start px-2 fw-bold">
            <label
              htmlFor="password"
              className="form-label"
              style={{ color: "GrayText" }}
            >
              비밀번호
            </label>
            <input
              type="password"
              className="form-control rounded-4"
              id="password"
              placeholder="비밀번호를 입력하세요"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            className="btn px-4 rounded-5 mt-4"
            style={{ backgroundColor: mainColor, color: "white" }}
          >
            회원가입
          </button>
        </form>
      </div>
      <footer className="bg-light py-4 w-100 text-center mt-4">
        <div className="container d-flex justify-content-center gap-3">
          <button
            onClick={() => navigate("/customer-support")}
            className="btn btn-link text-secondary"
          >
            고객센터
          </button>
          <button
            onClick={() => navigate("/terms")}
            className="btn btn-link text-secondary"
          >
            이용약관
          </button>
        </div>
        <div className="text-center mt-3">
          <p className="text-muted" style={{ fontSize: "12px" }}>
            © 2024 jobara Company. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default SignUpPage;
