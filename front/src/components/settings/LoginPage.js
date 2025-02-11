import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faEnvelope,
  faUserPlus,
  faQuestionCircle,
} from "@fortawesome/free-solid-svg-icons";
import { SiNaver, SiKakaotalk, SiGoogle } from "react-icons/si";
import { useNavigate } from "react-router-dom";

export const LoginPage = ({ handleSocialLogin, mainColor }) => {
  const navigate = useNavigate();

  return (
    <div className="bg-white p-4 rounded-3 shadow-sm">
      <h3 className="mb-4">로그인</h3>

      <div className="d-grid gap-2 mb-4">
        <button
          className="btn btn-light d-flex align-items-center justify-content-center gap-2 border"
          onClick={() => handleSocialLogin("Google")}
          style={{ height: "48px" }}
        >
          <SiGoogle className="text-danger" />
          구글 계정으로 로그인
        </button>
        <button
          className="btn btn-warning d-flex align-items-center justify-content-center gap-2"
          onClick={() => handleSocialLogin("Kakao")}
          style={{
            height: "48px",
            backgroundColor: "#FEE500",
            color: "#000000",
          }}
        >
          <SiKakaotalk />
          카카오톡 계정으로 로그인
        </button>
        <button
          className="btn d-flex align-items-center justify-content-center gap-2"
          onClick={() => handleSocialLogin("Naver")}
          style={{ height: "48px", backgroundColor: "#03C75A", color: "white" }}
        >
          <SiNaver />
          네이버 계정으로 로그인
        </button>
      </div>

      <div className="d-flex align-items-center mb-4">
        <div className="flex-grow-1 border-top"></div>
        <div className="px-3 text-muted">또는</div>
        <div className="flex-grow-1 border-top"></div>
      </div>

      <div className="d-grid gap-2">
        {[
          {
            icon: faEnvelope,
            text: "이메일로 로그인",
            path: "/email-login",
            primary: true,
          },
          { icon: faUserPlus, text: "이메일로 회원가입", path: "/signup" },
          { icon: faQuestionCircle, text: "문의하기", path: "/inquiry" },
        ].map((button, index) => (
          <button
            key={index}
            className={`btn ${
              button.primary
                ? ""
                : "btn-outline-" + (index === 1 ? "primary" : "secondary")
            } d-flex align-items-center justify-content-center gap-2`}
            style={{
              height: "48px",
              ...(button.primary && {
                backgroundColor: mainColor,
                color: "white",
              }),
            }}
            onClick={() => navigate(button.path)}
          >
            <FontAwesomeIcon icon={button.icon} />
            {button.text}
          </button>
        ))}
      </div>
    </div>
  );
};
