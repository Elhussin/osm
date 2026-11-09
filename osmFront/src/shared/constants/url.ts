import {
  FaLinkedin,
  FaGithub,
  FaWhatsapp,
  FaFacebook,
  FaTiktok,
  FaYoutube,
  FaInstagram,
  FaXTwitter,
} from "react-icons/fa6";
import { FiMail } from "react-icons/fi";



export const URLDATA = [
    { "path": "/", "name": "Home", },
    { "path": "/auth/login", "name": "Login", },
    { "path": "/auth/register", "name": "Register", },
    { "path": "/profile", "name": "Profile", },
    { "path": "/admin", "name": "Admin", },
    { "path": "/prescriptions", "name": "Prescriptions", },
    { "path": "/about", "name": "About", },
    { "path": "/contact", "name": "Contact", },
    { "path": "/users", "name": "Users", },
    { "path": "/tenants", "name": "Tenants", },
    { "path": "/groups", "name": "Groups", },
    { "path": "/crm", "name": "CRM", },
    { "path": "/products/supplier", "name": "Suppliers", },
  ]

export const navUrl=[
  {"path": "/", "name": "Home", },
  {"path": "/about", "name": "About", },
  {"path": "/contact", "name": "Contact", },
  {"path": "/privacy", "name": "Privacy", },
  {"path": "/terms", "name": "Terms", },
  {"path": "/faq", "name": "FAQ", },
  {"path": "/auth/register", "name": "Register", },  
]


export const socialLinks = [
  { url: "https://www.linkedin.com/in/osm-store-management/", icon: FaLinkedin, name: "LinkedIn" },
  { url: "https://www.github.com/osm-optics-store-management/", icon: FaGithub, name: "GitHub" },
  { url: "https://wa.me/+966540919725", icon: FaWhatsapp, name: "WhatsApp" },
  { url: "https://www.facebook.com/hasin.taha/", icon: FaFacebook, name: "Facebook" },
  { url: "https://www.tiktok.com/@hussaintaha9184", icon: FaTiktok, name: "TikTok" },
  { url: "https://www.youtube.com/@hussaintaha9184", icon: FaYoutube, name: "YouTube" },
  { url: "https://www.instagram.com/hasin.taha/", icon: FaInstagram, name: "Instagram" },
  { url: "https://www.twitter.com/hasin.taha/", icon: FaXTwitter, name: "X (Twitter)" },
  { url: "mailto:hasin3112@gmail.com", icon: FiMail, name: "Email" },
];

export const otherLinks = [
  { path: "/support", name: "Support" },
  { path: "/careers", name: "Careers" },
  { path: "/blog", name: "Blog" },
];