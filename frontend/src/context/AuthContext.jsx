import { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

const AuthContext = createContext();

const API_BASE_URL = 'http://localhost:8000/api';

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for saved token on initial load
        const token = localStorage.getItem('token');
        if (token) {
            fetchUser(token);
        } else {
            setLoading(false);
        }
    }, []);

    const fetchUser = async (token) => {
        try {
            const response = await axios.get(`${API_BASE_URL}/auth/me`, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            setUser(response.data);
        } catch (error) {
            console.error('Failed to fetch user', error);
            localStorage.removeItem('token');
        } finally {
            setLoading(false);
        }
    };

    const login = async (email, password) => {
        try {
            // OAuth2 expects form data for token requests
            const formData = new URLSearchParams();
            formData.append('username', email); // FastAPI OAuth2 expects 'username'
            formData.append('password', password);

            const response = await axios.post(`${API_BASE_URL}/auth/login`, formData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });

            const { access_token } = response.data;
            localStorage.setItem('token', access_token);
            await fetchUser(access_token);
            return { success: true };
        } catch (error) {
            const message = error.response?.data?.detail || 'Login failed';
            return { success: false, message };
        }
    };

    const register = async (name, email, password) => {
        try {
            await axios.post(`${API_BASE_URL}/auth/register`, {
                name,
                email,
                password
            });
            // Automatically login after successful registration
            return await login(email, password);
        } catch (error) {
            const message = error.response?.data?.detail || 'Registration failed';
            return { success: false, message };
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
