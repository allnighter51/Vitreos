import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface SentinelData {
  cpu: {
    totalLoad: number;
    temp: number;
    clock: number;
    cores: number[];
  };
  gpu: {
    load: number;
    vram: number;
    temp: number;
    coreClock: number;
    memClock: number;
    power: number;
  };
  memory: {
    used: number;
    total: number;
    speed: number;
  };
  storage: {
    drives: Array<{
      id: string;
      model: string;
      temp: number;
      health: number;
      read: number;
      write: number;
    }>;
  };
  network: {
    download: number;
    upload: number;
    ping: number;
  };
  security: {
    shieldLevel: number;
    activeThreats: number;
    breaches: Array<{
      timestamp: string;
      source: string;
      type: string;
      status: string;
    }>;
  };
  thermal: {
    motherboard: number;
    case: number;
    ambient: number;
  };
}

interface SentinelContextType {
  isConnected: boolean;
  data: SentinelData | null;
  connectionStatus: 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED' | 'ERROR';
  reconnect: () => void;
}

const SentinelContext = createContext<SentinelContextType | undefined>(undefined);

const WEBSOCKET_URL = 'ws://localhost:8000/sentinel';
const RECONNECT_INTERVAL = 5000;

export function SentinelProvider({ children }: { children: ReactNode }) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [data, setData] = useState<SentinelData | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'CONNECTING' | 'CONNECTED' | 'DISCONNECTED' | 'ERROR'>('DISCONNECTED');
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  const connect = () => {
    try {
      setConnectionStatus('CONNECTING');
      const socket = new WebSocket(WEBSOCKET_URL);

      socket.onopen = () => {
        console.log('[SENTINEL] WebSocket connection established');
        setIsConnected(true);
        setConnectionStatus('CONNECTED');
        setReconnectAttempt(0);
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          setData(payload);
        } catch (error) {
          console.error('[SENTINEL] Failed to parse message:', error);
        }
      };

      socket.onerror = (error) => {
        console.error('[SENTINEL] WebSocket error:', error);
        setConnectionStatus('ERROR');
      };

      socket.onclose = () => {
        console.log('[SENTINEL] WebSocket connection closed');
        setIsConnected(false);
        setConnectionStatus('DISCONNECTED');
        setWs(null);
        
        // Auto-reconnect after interval
        setTimeout(() => {
          setReconnectAttempt(prev => prev + 1);
        }, RECONNECT_INTERVAL);
      };

      setWs(socket);
    } catch (error) {
      console.error('[SENTINEL] Failed to create WebSocket:', error);
      setConnectionStatus('ERROR');
      setTimeout(() => {
        setReconnectAttempt(prev => prev + 1);
      }, RECONNECT_INTERVAL);
    }
  };

  const reconnect = () => {
    if (ws) {
      ws.close();
    }
    setReconnectAttempt(prev => prev + 1);
  };

  useEffect(() => {
    connect();
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [reconnectAttempt]);

  return (
    <SentinelContext.Provider value={{ isConnected, data, connectionStatus, reconnect }}>
      {children}
    </SentinelContext.Provider>
  );
}

export function useSentinel() {
  const context = useContext(SentinelContext);
  if (context === undefined) {
    throw new Error('useSentinel must be used within a SentinelProvider');
  }
  return context;
}
