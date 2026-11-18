import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Component, StrictMode, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router";
import { ApiError } from "./api/hooks";
import { AuthGate } from "./auth";
import { Layout } from "./components/Layout";
import { ErrorState, ToastProvider } from "./components/ui";
import { AdminPage } from "./pages/Admin";
import { AnnouncementsPage } from "./pages/Announcements";
import { CompetenciesPage } from "./pages/Competencies";
import { DashboardPage } from "./pages/Dashboard";
import { EventsPage } from "./pages/Events";
import { LoginPage } from "./pages/Login";
import { ProjectDetailPage, ProjectsPage } from "./pages/Projects";
import { ReportsPage } from "./pages/Reports";
import { SecurityPage } from "./pages/Security";
import { TokensPage } from "./pages/Tokens";
import { TasksPage } from "./pages/Tasks";
import "./styles.css";

document.documentElement.dataset.theme = localStorage.getItem("cth-theme") ?? "light";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000,
      refetchOnWindowFocus: false,
      retry: (count, err) => !(err instanceof ApiError && [401, 403, 404].includes(err.status)) && count < 2,
    },
  },
});

class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <ErrorState message="Bu ekranda beklenmeyen bir hata oluştu." onRetry={() => location.reload()} />
    ) : (
      this.props.children
    );
  }
}

function NotFound() {
  return <ErrorState message="Aradığınız sayfa bulunamadı." />;
}

const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: (
      <AuthGate>
        <Layout />
      </AuthGate>
    ),
    errorElement: <NotFound />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "tasks", element: <TasksPage /> },
      { path: "projects", element: <ProjectsPage /> },
      { path: "projects/:projectId", element: <ProjectDetailPage /> },
      { path: "events", element: <EventsPage /> },
      { path: "competencies", element: <CompetenciesPage /> },
      { path: "reports", element: <ReportsPage /> },
      { path: "announcements", element: <AnnouncementsPage /> },
      { path: "security", element: <SecurityPage /> },
      { path: "admin", element: <AdminPage /> },
      { path: "settings/tokens", element: <TokensPage /> },
      { path: "*", element: <NotFound /> },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <RouterProvider router={router} />
        </ToastProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>,
);
