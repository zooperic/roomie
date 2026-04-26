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
    timeout: 30000,
  });

  async getStatus(): Promise<AlfredStatus> {
    const { data } = await this.api.get('/health');
    return data;
  }

  async sendMessage(
    message: string,
    userId: string = 'web-user',
    forceAgent?: string,
    imageData?: string
  ): Promise<MessageResponse> {
    const { data } = await this.api.post('/message', {
      message,
      user_id: userId,
      force_agent: forceAgent,
      image_data: imageData,
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
    agent: 'fridge' | 'pantry'
  ): Promise<MessageResponse> {
    const { data } = await this.api.post(`/inventory/${agent}`, item);
    return data;
  }

  async updateInventoryItem(
    id: number,
    item: Partial<InventoryItem>,
    agent: 'fridge' | 'pantry'
  ): Promise<MessageResponse> {
    const { data } = await this.api.put(`/inventory/${agent}/${id}`, item);
    return data;
  }

  async deleteInventoryItem(
    id: number,
    agent: 'fridge' | 'pantry'
  ): Promise<MessageResponse> {
    const { data } = await this.api.delete(`/inventory/${agent}/${id}`);
    return data;
  }

  async parseRecipe(input: string, mode: 'url' | 'text' | 'dish'): Promise<MessageResponse> {
    let message = '';
    if (mode === 'url') {
      message = `parse this recipe: ${input}`;
    } else if (mode === 'text') {
      message = `parse this recipe:\n${input}`;
    } else {
      message = `I want to make ${input}`;
    }

    return this.sendMessage(message, 'web-user', 'remy');
  }

  async buildCart(items: Array<{ name: string; quantity?: number; unit?: string }>): Promise<MessageResponse> {
    const itemList = items.map(i =>
      i.quantity ? `${i.name} ${i.quantity}${i.unit || ''}` : i.name
    ).join(', ');

    return this.sendMessage(`find these on swiggy: ${itemList}`, 'web-user', 'lebowski');
  }

  async parseRecipe(input: string, type: 'url' | 'text' | 'dish'): Promise<MessageResponse> {
    let message = '';
    switch (type) {
      case 'url':
        message = `can I make this? ${input}`;
        break;
      case 'text':
        message = `parse this recipe: ${input}`;
        break;
      case 'dish':
        message = `can I make ${input}?`;
        break;
    }
    return this.sendMessage(message, 'web-user', 'remy');
  }

  async buildCart(items: string[]): Promise<MessageResponse> {
    const message = `find on swiggy: ${items.join(', ')}`;
    return this.sendMessage(message, 'web-user', 'lebowski');
  }

  async getEvents(limit: number = 10): Promise<Event[]> {
    // This would need a proper events endpoint on Alfred
    // For now, return empty array
    return [];
  }
}

export const alfredClient = new AlfredClient();
