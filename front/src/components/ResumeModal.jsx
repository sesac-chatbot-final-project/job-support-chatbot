import React from "react";

const ResumeModal = ({ resume, onClose }) => {
  if (!resume) return null;

  return (
    <div
      className="modal show d-flex align-items-center justify-content-center"
      style={{
        display: "block",
        backgroundColor: "rgba(0,0,0,0.5)",
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        zIndex: 1050,
        overflowY: "auto", // 화면 크기에 따라 스크롤 가능
      }}
    >
      <div
        className="modal-dialog"
        style={{
          maxWidth: "600px",
          width: "90%",
          margin: "10vh auto", // 화면 중앙 정렬
        }}
      >
        <div
          className="modal-content p-4"
          style={{
            backgroundColor: "#ffffff",
            borderRadius: "15px",
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
            padding: "20px",
            overflow: "hidden",
            maxHeight: "80vh", // 모달이 너무 크면 잘리지 않고 스크롤 가능
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* 모달 헤더 */}
          <div
            className="modal-header border-0"
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <h5
              className="modal-title"
              style={{ fontSize: "1.5rem", fontWeight: "bold" }}
            >
              자기소개서 상세보기
            </h5>
            <button
              type="button"
              className="btn-close"
              onClick={onClose}
              style={{
                fontSize: "1.2rem",
                cursor: "pointer",
                background: "none",
                border: "none",
              }}
            ></button>
          </div>

          {/* 모달 본문 */}
          <div
            className="modal-body"
            style={{
              overflowY: "auto", // 긴 내용이 있을 경우 스크롤 허용
              flex: 1,
            }}
          >
            <p
              style={{
                fontSize: "1.1rem",
                lineHeight: "1.6",
                color: "#333",
                whiteSpace: "pre-line",
              }}
            >
              {resume.content}
            </p>
            <p className="text-end text-muted mt-3">
              <small>작성일: {resume.date}</small>
            </p>
          </div>

          {/* 모달 푸터 */}
          <div className="modal-footer d-flex justify-content-end">
            <button
              className="btn"
              onClick={onClose}
              style={{
                backgroundColor: "#5e6aec",
                color: "white",
                borderRadius: "25px",
                padding: "8px 20px",
                fontSize: "1rem",
                transition: "background-color 0.3s",
              }}
              onMouseEnter={(e) => (e.target.style.backgroundColor = "#5a6268")}
              onMouseLeave={(e) => (e.target.style.backgroundColor = "#6c757d")}
            >
              닫기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResumeModal;
