import {AppRouter} from "@app/routes/AppRouter.tsx";
import { loadSessionUser, useSessionStore } from "@entities/user";
import {useEffect} from "react";
import {Provider} from "@app/providers/provider.tsx";

function App() {
  const setUser = useSessionStore((s) => s.setUser);
  const setLoading = useSessionStore((s) => s.setLoading);

  useEffect(() => {
    const refreshToken = localStorage.getItem('refresh_token');

    if (!refreshToken) {
      setUser(null);
      setLoading(false);
      return;
    }

    void loadSessionUser().catch(() => {
      localStorage.removeItem('refresh_token');
      setUser(null);
      setLoading(false);
    });
  }, [setUser, setLoading]);

  return (
    <Provider>
      <AppRouter />
    </Provider>
  )
}

export default App;