// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDZJf6BphFYRiGxami60J_St7zXpL6Jw5o",
  authDomain: "nfl-lms.firebaseapp.com",
  projectId: "nfl-lms",
  storageBucket: "nfl-lms.firebasestorage.app",
  messagingSenderId: "644268342508",
  appId: "1:644268342508:web:68fddcdd2a8d3df01b39c9",
  measurementId: "G-BS3VLFGN82",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

export { analytics, app };
