import {createBrowserRouter, RouterProvider} from "react-router";
import {LandingPage} from "@pages/landing/ui/LandingPage";
import {LoginPage} from "@pages/login/ui/LoginPage.tsx";
import {RegisterPage} from "@pages/register/ui/RegisterPage.tsx";
import {PetsPage} from "@pages/pets/ui/PetsPage.tsx";
import {PetPage} from "@pages/pet/ui/PetPage.tsx";
import {ProfilePage} from "@pages/profile/ui/ProfilePage.tsx";
import {AdminPage} from "@pages/admin/ui/AdminPage.tsx";
import {AdminUserPage} from "@pages/admin-users/ui/AdminUserPage.tsx";
import {VerifyEmailPage} from "@pages/verify-email/ui/VerifyEmailPage.tsx";
import {
  RecoverAccountPage
} from "@pages/recover-account/ui/RecoverAccountPage.tsx";
import {NotFound} from "@pages/not-found/ui/NotFound.tsx";
import {PublicRoute, PrivateRoute, AdminRoute} from "@app/routes/RouteGuards";

const router = createBrowserRouter([
  {
    path:'/',
    element: <PublicRoute><LandingPage /></PublicRoute>
  },
  {
    path: '/login',
    element: <PublicRoute><LoginPage /></PublicRoute>
  },
  {
    path: '/register',
    element: <PublicRoute><RegisterPage /></PublicRoute>
  },
  {
    path: '/pets',
    element: <PrivateRoute><PetsPage /></PrivateRoute>
  },
  {
    path: '/pet/:petId',
    element: <PrivateRoute><PetPage /></PrivateRoute>
  },
  {
    path: '/profile',
    element: <PrivateRoute><ProfilePage /></PrivateRoute>
  },
  {
    path: '/admin',
    element: <AdminRoute><AdminPage /></AdminRoute>
  },
  {
    path: '/admin-user',
    element: <AdminRoute><AdminUserPage /></AdminRoute>
  },
  {
    path: '/verify-email',
    element: <PublicRoute><VerifyEmailPage /></PublicRoute>
  },
  {
    path: '/recovery-account',
    element: <PublicRoute><RecoverAccountPage /></PublicRoute>
  },
  {
    path: '*',
    element: <NotFound />
  }
])

export const AppRouter = () => {
  return <RouterProvider router={router} />
}