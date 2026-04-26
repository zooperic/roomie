import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_ALFRED_API || 'http://localhost:8000';

export interface AlfredStatus {
  status: string;
  agents: {
    [key: string]: {
      healthy: boolean;
      summary?: string;
    };
  };
}

export interface InventoryItem {
  id?: number;
  name: string;
  quantity: number;
  unit: string;
  category?: string;
  low_stock_threshold?: number;
  last_updated?: string;
}

export interface MessageResponse {
  response: string;
  agent_used?: string;
  action_type?: string;
  // The actual structured result from the agent (recipe parse, cart, etc.)
  result?: unknown;
  suggested_action?: string;
  suggested_action_payload?: unknown;
}

export interface Event {
  timestamp: string;
  agent: string;
  type: string;
  detail: string;
}

class AlfredClient {
  private api = axios.create({
    baseURL: API_BASE,
    timeout: 220000,  // 3min 40s — gives server's 180s timeout room to respond cleanly
  });

  async getStatus(): Promise<AlfredStatus> {
    const { data } = await this.api.get('/health');
    return data;
  }

  async sendMessage(
    message: string,
    userId: string = 'web-user',
    forceAgent?: string,
    imageData?: string,
    parameters?: Record<string, unknown>,
  ): Promise<MessageResponse> {
    const { data } = await this.api.post('/message', {
      message,
      user_id: userId,
      force_agent: forceAgent,
      image_data: imageData,
      parameters,
    });
    return data;
  }

  async getFridgeInventory(): Promise<InventoryItem[]> {
    const { data } = await this.api.get('/inventory/fridge');
    return data;
  }

  async getPantryInventory(): Promise<InventoryItem[]> {
    const { data } = await this.api.get('/inventory/pantry');
    return data;
  }

  async addInventoryItem(
    item: Partial<InventoryItem>,
    agent: 'fridge' | 'pantry',
  ): Promise<MessageResponse> {
    const { data } = await this.api.post(`/inventory/${agent}`, item);
    return data;
  }

  async updateInventoryItem(
    id: number,
    item: Partial<InventoryItem>,
    agent: 'fridge' | 'pantry',
  ): Promise<MessageResponse> {
    const { data } = await this.api.put(`/inventory/${agent}/${id}`, item);
    return data;
  }

  async deleteInventoryItem(
    id: number,
    agent: 'fridge' | 'pantry',
  ): Promise<MessageResponse> {
    const { data } = await this.api.delete(`/inventory/${agent}/${id}`);
    return data;
  }

  /**
   * Parse a recipe via the direct /recipes/parse endpoint.
   * Bypasses Alfred's LLM router — saves 30-120s, eliminates routing errors.
   */
  async parseRecipe(
    input: string,
    mode: 'url' | 'text' | 'dish',
    servings?: number,
  ): Promise<{ result: unknown; suggested_action?: string; suggested_action_payload?: unknown; error?: string }> {
    const { data } = await this.api.post('/recipes/parse', {
      input,
      mode,
      servings: servings || null,
    });
    return data;
  }

  /**
   * Build a Swiggy cart via Lebowski from a list of items.
   */
  async buildCart(
    items: Array<{ name: string; quantity?: number; unit?: string }>,
  ): Promise<MessageResponse> {
    const { data } = await this.api.post('/build_cart', { items });
    return data;
  }

  async getEvents(limit: number = 10): Promise<Event[]> {
    return [];
  }
}

export const alfredClient = new AlfredClient();
