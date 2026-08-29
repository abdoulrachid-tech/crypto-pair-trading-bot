import { render, screen } from '@testing-library/react';
import { describe, test, expect } from 'vitest';
import TradeTable from '../components/TradeTable';

const sampleTrades = [
  {
    _id: '1', symbolA: 'BTC/USDT', symbolB: 'ETH/USDT', signal: 'close',
    priceA: 65000, priceB: 3400, zscore: 0.234, pnl: 12.5, mode: 'simulation',
    executedAt: '2024-01-01T10:00:00Z',
  },
  {
    _id: '2', symbolA: 'BTC/USDT', symbolB: 'ETH/USDT', signal: 'long',
    priceA: 64000, priceB: 3300, zscore: -2.1, pnl: null, mode: 'simulation',
    executedAt: '2024-01-01T09:00:00Z',
  },
];

describe('TradeTable', () => {
  test('affiche un message vide quand il n\'y a aucun trade', () => {
    render(<TradeTable trades={[]} />);
    expect(screen.getByText(/Aucun trade enregistré/)).toBeInTheDocument();
  });

  test('affiche les lignes de trades avec les bonnes valeurs', () => {
    render(<TradeTable trades={sampleTrades} />);
    const pairCells = screen.getAllByText((content) => content.includes('BTC/USDT') && content.includes('ETH/USDT'));
    expect(pairCells.length).toBeGreaterThan(0);
    expect(screen.getByText('close')).toBeInTheDocument();
    expect(screen.getByText('long')).toBeInTheDocument();
    expect(screen.getByText('12.50')).toBeInTheDocument();
  });

  test('affiche un tiret pour un PnL non défini (position encore ouverte)', () => {
    render(<TradeTable trades={sampleTrades} />);
    const cells = screen.getAllByText('—');
    expect(cells.length).toBeGreaterThan(0);
  });
});
