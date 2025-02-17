// components/LoginPage.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const LoginPage = () => {
  const navigate = useNavigate();
  const mainColor = "#5e6aec";
  const [credentials, setCredentials] = useState({
    username: "",
    password: "",
  });
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCredentials((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch("http://localhost:8000/api/users/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
      });
      if (!response.ok) {
        const data = await response.json();
        setError(data.error || "로그인 실패");
        return;
      }
      const data = await response.json();
      // 토큰과 사용자 정보를 localStorage에 저장
      localStorage.setItem("token", data.token);
      localStorage.setItem("userProfile", JSON.stringify(data.userProfile));
      navigate("/settings");
    } catch (error) {
      console.error(error);
      setError("로그인 요청 중 오류가 발생했습니다.");
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
        className="bg-white p-5 rounded-5 shadow-lg text-center"
        style={{
          width: "500px",
          margin: "0 auto",
          marginTop: "50px",
          fontFamily: "Nanum Gothic",
        }}
      >
        <h3 className="mb-4 text-center" style={{ color: "GrayText" }}>
          <strong>로그인</strong>
        </h3>
        {error && <div className="alert alert-danger">{error}</div>}
        <form onSubmit={handleSubmit}>
        <div className="mb-3 text-start px-2 fw-bold">
            <label
              htmlFor="username"
              className="form-label"
              style={{ color: "GrayText" }}
            >아이디</label>
            <input
              type="text"
              name="username"
              className="form-control rounded-4"
              placeholder="아이디를 입력하세요"
              value={credentials.username}
              onChange={handleChange}
              required
            />
          </div>
          <div className="mb-3 text-start px-2 fw-bold">
            <label
              htmlFor="username"
              className="form-label"
              style={{ color: "GrayText" }}
            >비밀번호</label>
            <input
              type="password"
              name="password"
              className="form-control rounded-4"
              placeholder="비밀번호를 입력하세요"
              value={credentials.password}
              onChange={handleChange}
              required
            />
          </div>
          <div className="d-flex justify-content-center">
            <button
              type="submit"
              className="btn px-4 rounded-5"
              style={{ backgroundColor: mainColor, color: "white" }}
            >
              로그인
            </button>
          </div>
        </form>
      </div>

      {/* Footer */}
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

export default LoginPage;
