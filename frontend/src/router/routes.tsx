import NotFound from '@/pages/404'
import CreativePage from '@/pages/creative'
import {
  Navigate,
  Outlet,
  RouteObject,
  createBrowserRouter,
} from 'react-router-dom'

export type IRouteObject = {
  children?: IRouteObject[]
  name?: string
  auth?: boolean
  pure?: boolean
  meta?: any
} & Omit<RouteObject, 'children'>

export const routes: IRouteObject[] = [
  {
    path: '/',
    element: <Navigate to="/creative" replace />,
  },
  {
    path: '/creative',
    Component: CreativePage,
  },
  {
    path: '/404',
    Component: NotFound,
    pure: true,
  },
]

export const router = createBrowserRouter(
  [
    {
      path: '/',
      element: <Outlet />,
      children: routes,
    },
    {
      path: '*',
      element: <Navigate to="/creative" />,
    },
  ] as RouteObject[],
  {
    basename: import.meta.env.BASE_URL,
  },
)
