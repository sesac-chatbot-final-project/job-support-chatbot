import React from "react";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";

const CustomerSupport = () => {
  const navigate = useNavigate();
  const mainColor = "#5e6aec";
  return (
    <div
      className="d-flex flex-column min-vh-100"
      style={{ width: "100vw", maxWidth: "none" }}
    >
      {/* Header */}
      <header
        className="d-flex justify-content-between align-items-center px-4 py-3 w-100"
        style={{ backgroundColor: mainColor }}
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
      </header>
      <h3 className="text-center mb-4">고객 지원</h3>
      <p className="lead text-center">
        도움이 필요하시면 지원 팀에 연락해 주세요.
      </p>

      <div className="row">
        <div className="col-md-6">
          <h3>연락처</h3>
          <ul className="list-unstyled">
            <li>
              <strong>이메일:</strong> support@jobara.com
            </li>
            <li>
              <strong>전화:</strong> +1 234 567 890
            </li>
          </ul>
        </div>

        <div className="col-md-6">
          <h3>자주 묻는 질문 (FAQ)</h3>
          <ul className="list-group">
            <li className="list-group-item">비밀번호를 어떻게 재설정하나요?</li>
            <li className="list-group-item">프로필을 어떻게 업데이트하나요?</li>
            <li className="list-group-item">
              내 과거 지원서를 어디에서 확인할 수 있나요?
            </li>
          </ul>
        </div>

        {/* Footer */}
        <footer className="bg-light py-4 w-100">
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
    </div>
  );
};

export default CustomerSupport;
