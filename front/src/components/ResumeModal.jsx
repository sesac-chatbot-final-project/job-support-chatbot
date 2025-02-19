import React from "react";

const ResumeModal = ({ resume, onClose }) => {
  if (!resume) return null;

  return (
    <div
      className="modal show"
      style={{ display: "block", backgroundColor: "rgba(0,0,0,0.5)" }}
    >
      <div className="modal-dialog">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">자기소개서 상세보기</h5>
            <button
              type="button"
              className="btn-close"
              onClick={onClose}
            ></button>
          </div>
          <div className="modal-body">
            {/* 여기서 자소서 본문(content)을 표시 */}
            <p>{resume.content}</p>
            <p>
              <small>작성일: {resume.date}</small>
            </p>
          </div>
          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={onClose}>
              닫기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResumeModal;
