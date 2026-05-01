import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API, timeout: 180000 });

export const fileToBase64 = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const str = reader.result;
      const comma = str.indexOf(",");
      resolve(comma >= 0 ? str.slice(comma + 1) : str);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
