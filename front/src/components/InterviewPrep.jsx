import React from "react";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHome } from "@fortawesome/free-solid-svg-icons";

const InterviewPrep = () => {
  const navigate = useNavigate();
  const mainColor = "#5e6aec";

  const commonQuestions = [
    {
      question: "자신의 장단점은 무엇인가요?",
      tip: "장점은 구체적인 사례와 함께 설명하고, 단점은 극복 노력을 함께 언급하세요.",
    },
    {
      question: "우리 회사에 지원한 이유는 무엇인가요?",
      tip: "회사의 비전, 문화, 제품/서비스에 대한 구체적인 리서치를 바탕으로 답변하세요.",
    },
    {
      question: "스트레스 상황을 어떻게 극복하시나요?",
      tip: "실제 경험을 바탕으로 문제 해결 과정과 결과를 구체적으로 설명하세요.",
    },
  ];

  return (
    <div
      className="d-flex flex-column min-vh-100"
      style={{ width: "100vw", maxWidth: "none" }}
    >
      {/* Header */}
      <header
        className="d-flex justify-content-between align-items-center px-3 px-md-5 py-3 container-fluid"
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
      <main className="flex-grow-1 container py-5">
        <h3 className="text-center fw-bold mb-4" style={{ color: mainColor }}>
          면접 준비 가이드
        </h3>

        <div className="row g-4 mb-4">
          <div className="col-md-6">
            <div className="card shadow-sm p-3 border-0 rounded-4">
              <div className="card-body">
                <h3 className="fs-5 fw-bold mb-3" style={{ color: mainColor }}>
                  면접 준비 체크리스트
                </h3>
                <ul className="list-unstyled text-muted">
                  <li>• 회사 정보 및 최근 뉴스 숙지</li>
                  <li>• 직무 관련 전문 지식 복습</li>
                  <li>• 예상 질문 답변 준비</li>
                  <li>• 복장 및 준비물 체크</li>
                </ul>
              </div>
            </div>
          </div>
          <div className="col-md-6">
            <div className="card shadow-sm p-3 border-0 rounded-4">
              <div className="card-body">
                <h3 className="fs-5 fw-bold mb-3" style={{ color: mainColor }}>
                  면접 당일 유의사항
                </h3>
                <ul className="list-unstyled text-muted">
                  <li>• 시간 여유 있게 도착 (30분 전)</li>
                  <li>• 바른 자세와 밝은 표정 유지</li>
                  <li>• 경청하고 명확하게 답변</li>
                  <li>• 예의 바른 태도로 임하기</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 bg-light rounded-4">
          <h5 className="fw-bold mb-3 px-4 py-2" style={{ color: mainColor }}>
            자주 나오는 질문과 답변 팁
          </h5>
          <div className="row g-3">
            {commonQuestions.map((item, index) => (
              <div key={index} className="col-md-4">
                <div className="p-3 bg-white rounded-4 shadow-sm">
                  <h3
                    className="fs-6 fw-bold mb-2 px-2 mt-2"
                    style={{ color: "GrayText" }}
                  >
                    Q. {item.question}
                  </h3>
                  <p className="text-muted mt-3 px-2">💡 {item.tip}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-light py-4">
        <div className="container d-flex justify-content-center gap-3">
          <button
            onClick={() => navigate("/customer-support")}
            className="btn btn-link text-secondary"
            style={{ fontSize: "16px", lineHeight: "1.1" }}
          >
            고객센터
          </button>
          <button
            onClick={() => navigate("/terms")}
            className="btn btn-link text-secondary"
            style={{ fontSize: "16px", lineHeight: "1.1" }}
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

export default InterviewPrep;
