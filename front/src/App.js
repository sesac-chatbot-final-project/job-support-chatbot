import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Main from "./components/Main";
import Chatbot from "./components/Chatbot";
import Settings from "./components/Settings";
import { SignUpPage } from "./components/settings/Signup"; // 회원가입 페이지 import
import LoginPage from "./components/LoginPage"; // 로그인 페이지 컴포넌트 추가
import ResumeGuide from "./components/ResumeGuide";
import InterviewPrep from "./components/InterviewPrep";
import PortfolioGuide from "./components/PortfolioGuide";
import CustomerSupport from "./components/CustomerSupport";
import Terms from "./components/Terms";
import "bootstrap/dist/css/bootstrap.min.css";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Main />} />
        <Route path="/chatbot" element={<Chatbot />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/signup" element={<SignUpPage />} />{" "}
        <Route path="/login" element={<LoginPage />} />{" "}
        <Route path="/resume-guide" element={<ResumeGuide />} />
        <Route path="/interview-prep" element={<InterviewPrep />} />
        <Route path="/portfolio-guide" element={<PortfolioGuide />} />
        <Route path="/customer-support" element={<CustomerSupport />} />
        <Route path="/terms" element={<Terms />} />
      </Routes>
    </Router>
  );
}

export default App;
