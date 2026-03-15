import { Link } from "react-router-dom";
import { Breadcrumb } from "./Breadcrumb";
import logoSrc from "../../assets/logo.png";
import "./Header.css";

export function Header() {
  return (
    <header className="ace-header">
      <Link to="/garage" className="ace-header__brand">
        <img src={logoSrc} alt="AC Race Engineer" className="ace-header__logo" />
        <span className="ace-header__title">AC Race Engineer</span>
      </Link>
      <div className="ace-header__breadcrumb">
        <Breadcrumb />
      </div>
      <Link to="/settings" className="ace-header__settings" aria-label="Settings">
        <i className="fa-solid fa-gear" />
      </Link>
    </header>
  );
}
