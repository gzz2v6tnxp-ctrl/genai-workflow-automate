import { useState, useEffect } from 'react';

const useResponsive = () => {
    const [isMobile, setIsMobile] = useState(false);

    const handleResize = () => {
        setIsMobile(window.innerWidth <= 768);
    };

    useEffect(() => {
        handleResize(); // set initial state
        window.addEventListener('resize', handleResize);

        return () => { // cleanup listener on unmount
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    return { isMobile };
};

export default useResponsive;