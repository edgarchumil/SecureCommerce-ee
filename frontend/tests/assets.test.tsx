import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getAssets } from "../src/api/assets";
import { AssetsPage } from "../src/pages/AssetsPage";
import { assetSchema } from "../src/schemas/assets";

vi.mock("../src/api/assets", () => ({
  getAssets: vi.fn(),
  deleteAsset: vi.fn(),
}));

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <AssetsPage />
      </BrowserRouter>
    </QueryClientProvider>,
  );
}

describe("inventario de activos", () => {
  beforeEach(() => vi.mocked(getAssets).mockReset());

  it("muestra un estado vacío comprensible", async () => {
    vi.mocked(getAssets).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      pages: 0,
    });
    renderPage();
    expect(await screen.findByText("Aún no hay activos")).toBeInTheDocument();
  });

  it("valida criticidad e IP", () => {
    const result = assetSchema.safeParse({
      name: "Servidor",
      internal_code: "SRV-01",
      asset_type: "server",
      exposure_level: "internal",
      status: "active",
      ip_address: "999.1.1.1",
      confidentiality_criticality: 6,
      integrity_criticality: 3,
      availability_criticality: 3,
    });
    expect(result.success).toBe(false);
  });
});
