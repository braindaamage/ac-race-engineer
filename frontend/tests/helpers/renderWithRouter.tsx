import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

export function renderWithRouter(
  element: React.ReactElement,
  {
    route = "/",
    path = "/",
    routes,
  }: {
    route?: string;
    path?: string;
    routes?: Array<{ path: string; element: React.ReactElement }>;
  } = {},
) {
  const routeConfig = routes ?? [{ path, element }];
  const router = createMemoryRouter(routeConfig, {
    initialEntries: [route],
  });
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return {
    ...render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    ),
    router,
    queryClient,
  };
}
