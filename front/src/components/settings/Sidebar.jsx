import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faUser,
  faFileAlt,
  faComments,
  faBriefcase,
} from "@fortawesome/free-solid-svg-icons";

export const Sidebar = ({ activeTab, setActiveTab, isLoggedIn, mainColor }) => {
  const menuItems = [
    { id: "profile", icon: faUser, text: "내 정보" },
    { id: "resumes", icon: faFileAlt, text: "작성된 자기소개서" },
    { id: "interviews", icon: faComments, text: "면접 연습 내역" },
    { id: "jobs", icon: faBriefcase, text: "확인한 채용공고" },
  ];

  return (
    <div className="list-group w-100">
      {menuItems.map((item) => (
        <button
          key={item.id}
          className={`list-group-item list-group-item-action ${
            activeTab === item.id ? "active" : ""
          }`}
          onClick={() => setActiveTab(item.id)}
          style={{
            backgroundColor: activeTab === item.id ? mainColor : "",
            color: activeTab === item.id ? "white" : "",
            borderColor: activeTab === item.id ? mainColor : "",
          }}
          disabled={item.id !== "profile" && !isLoggedIn}
        >
          <FontAwesomeIcon icon={item.icon} className="me-2" />
          {item.text}
        </button>
      ))}
    </div>
  );
};
