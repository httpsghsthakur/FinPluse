import React, { useEffect, useRef } from 'react';
import { useAuth } from '../layout/AuthProvider';

export const BiometricCollector: React.FC = () => {
  const { user } = useAuth();
  const typingCadence = useRef<number[]>([]);
  const mouseVelocity = useRef<number[]>([]);
  const lastKeyTime = useRef<number>(0);
  const lastMousePos = useRef<{x: number, y: number, t: number} | null>(null);

  useEffect(() => {
    if (!user) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const now = performance.now();
      if (lastKeyTime.current > 0) {
        const interval = now - lastKeyTime.current;
        if (interval < 1000) { // Only count if < 1s to avoid idle gaps
          typingCadence.current.push(interval);
        }
      }
      lastKeyTime.current = now;
    };

    const handleMouseMove = (e: MouseEvent) => {
      const now = performance.now();
      if (lastMousePos.current) {
        const dt = now - lastMousePos.current.t;
        if (dt > 50) { // Sample every 50ms
          const dx = e.clientX - lastMousePos.current.x;
          const dy = e.clientY - lastMousePos.current.y;
          const dist = Math.sqrt(dx*dx + dy*dy);
          const velocity = (dist / dt) * 1000; // pixels per second
          mouseVelocity.current.push(velocity);
          
          lastMousePos.current = { x: e.clientX, y: e.clientY, t: now };
        }
      } else {
        lastMousePos.current = { x: e.clientX, y: e.clientY, t: now };
      }
    };

    const submitBiometrics = async () => {
      if (typingCadence.current.length === 0 && mouseVelocity.current.length === 0) return;
      
      const payload = {
        user_id: user.id,
        session_id: "sess_" + Math.random().toString(36).substr(2, 9),
        typing_cadence: typingCadence.current.slice(-50), // keep last 50
        mouse_velocity: mouseVelocity.current.slice(-50),
        scroll_behavior: { bounces: 0 }, // Mock
        time_of_day: new Date().getHours()
      };

      try {
        await fetch(import.meta.env.VITE_API_BASE_URL + '/security/biometrics/log', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(payload)
        });
      } catch (err) {
        console.error("Failed to log biometrics", err);
      }

      // Clear buffers
      typingCadence.current = [];
      mouseVelocity.current = [];
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('mousemove', handleMouseMove);
    
    // Submit every 30 seconds
    const interval = setInterval(submitBiometrics, 30000);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('mousemove', handleMouseMove);
      clearInterval(interval);
    };
  }, [user]);

  return null; // Invisible component
};
