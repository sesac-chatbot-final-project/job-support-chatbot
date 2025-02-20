import React from "react";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHome } from "@fortawesome/free-solid-svg-icons";

const Terms = () => {
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

      {/* 이용 약관 내용 */}
      <div className="flex-grow-1 d-flex flex-column align-items-center">
        <h3
          className="text-center mt-5 py-2 w-100"
          style={{ color: "GrayText" }}
        >
          <strong>이용 약관</strong>
        </h3>

        <p
          className="lead text-center px-5"
          style={{ color: "GrayText", fontSize: "1.1rem" }}
        >
          서비스를 사용하기 전에 아래 이용 약관을 잘 읽어주세요.
        </p>

        <div className="w-90 px-5 px-md-5" style={{ color: "GrayText" }}>
          <h5>
            <strong>1. 약관 동의</strong>
          </h5>
          <p>
            본 웹사이트에 접속하고 사용하는 것은 이 이용 약관에 동의하는 것으로
            간주됩니다.
          </p>

          <h5>
            <strong>2. 개인정보 처리 방침</strong>
          </h5>
          <p>
            귀하의 개인정보는 중요하게 다뤄지며, 개인정보 처리 방침을 통해
            데이터를 어떻게 수집하고 사용하는지 확인할 수 있습니다.
          </p>

          <h5>
            <strong>3. 사용자 의무</strong>
          </h5>
          <p>
            귀하는 불법적인 목적으로 서비스를 사용하거나 서비스에 손해를 주는
            방식으로 사용하지 않을 것에 동의합니다.
          </p>

          <h5>
            <strong>4. 책임 제한</strong>
          </h5>
          <p>
            본 웹사이트를 사용함으로 인해 발생한 직접적, 간접적, 우발적,
            결과적인 손해에 대해 당사는 책임을 지지 않습니다.
          </p>

          <h5>
            <strong>5. 약관 변경</strong>
          </h5>
          <p>
            당사는 이 약관을 수시로 업데이트할 수 있으며, 귀하는 정기적으로
            약관을 검토할 책임이 있습니다.
          </p>
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
    </div>
  );
};

export default Terms;
