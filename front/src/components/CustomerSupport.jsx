import React from "react";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHome } from "@fortawesome/free-solid-svg-icons";

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
          style={{ cursor: "pointer" }}
        />
        <button onClick={() => navigate("/")} className="btn rounded-5 fw-bold">
          <FontAwesomeIcon
            icon={faHome}
            style={{
              color: "white",
              border: "none",
              width: "1.4rem",
              height: "1.4rem",
            }}
          />
        </button>
      </header>
      <h3 className="text-center mt-5 py-2 w-100" style={{ color: "GrayText" }}>
        <strong>고객 지원 센터</strong>
      </h3>
      <p
        className="lead text-center px-5"
        style={{ color: "GrayText", fontSize: "1.1rem" }}
      >
        도움이 필요하시면 지원 팀에 연락해 주세요.
      </p>

      <div
        className="d-flex flex-column align-items-center"
        style={{ color: "GrayText" }}
      >
        {/* 자주 묻는 질문(FAQ) */}
        <div className="col-md-8 px-5 py-4 mt-2 mb-2">
          <h5>
            <strong>자주 묻는 질문 (FAQ)</strong>
          </h5>
          <ul className="list-group mt-3" style={{ color: "GrayText" }}>
            <li className="list-group-item" style={{ color: "GrayText" }}>
              비밀번호를 어떻게 재설정하나요?
            </li>
            <li className="list-group-item" style={{ color: "GrayText" }}>
              프로필을 어떻게 업데이트하나요?
            </li>
            <li className="list-group-item" style={{ color: "GrayText" }}>
              내 과거 지원서를 어디에서 확인하나요?
            </li>
          </ul>
        </div>

        {/* 연락처 */}
        <div className="col-md-8 px-5 py-2">
          <h5>
            <strong>연락처</strong>
          </h5>
          <ul className="list-unstyled">
            <li>
              <strong>이메일:</strong> support@jobara.com
            </li>
            <li>
              <strong>전화:</strong> +1 234 567 890
            </li>
          </ul>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-light mt-5 py-4 w-100">
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

export default CustomerSupport;
