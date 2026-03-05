import { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'

export default function App() {
    return (
        <Routes>
            <Route path="/" element={<Dashboard />} />
        </Routes>
    )
}
