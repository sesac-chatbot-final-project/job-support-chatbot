// components/LoginPage.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const LoginPage = () => {
  const navigate = useNavigate();
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
      className="bg-white p-4 rounded-3 shadow-sm"
      style={{ maxWidth: "400px", margin: "auto" }}
    >
      <h3 className="mb-4 text-center">로그인</h3>
      {error && <div className="alert alert-danger">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="form-label">아이디</label>
          <input
            type="text"
            name="username"
            className="form-control"
            placeholder="아이디를 입력하세요"
            value={credentials.username}
            onChange={handleChange}
            required
          />
        </div>
        <div className="mb-3">
          <label className="form-label">비밀번호</label>
          <input
            type="password"
            name="password"
            className="form-control"
            placeholder="비밀번호를 입력하세요"
            value={credentials.password}
            onChange={handleChange}
            required
          />
        </div>
        <button
          type="submit"
          className="btn w-100"
          style={{ backgroundColor: "#5e6aec", color: "white" }}
        >
          로그인
        </button>
      </form>
    </div>
  );
};

export default LoginPage;
