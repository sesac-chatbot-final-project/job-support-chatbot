import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowLeft } from "@fortawesome/free-solid-svg-icons";
import { useNavigate } from "react-router-dom";

export const Header = ({ mainColor }) => {
  const navigate = useNavigate();

  return (
    <header
      className="d-flex align-items-center justify-content-between text-white px-3 py-2"
      style={{
        backgroundColor: mainColor,
        width: "100%",
      }}
    >
      <div className="d-flex align-items-center">
        <img
          src="/images/logo.png"
          alt="Company Logo"
          className="me-3"
          style={{ width: "150px", height: "60px" }}
        />
      </div>
      <button
        className="btn btn-link text-white"
        onClick={() => navigate("/chatbot")}
      >
        <FontAwesomeIcon icon={faArrowLeft} className="me-2" />
      </button>
    </header>
  );
};
