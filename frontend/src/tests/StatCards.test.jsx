import { render, screen } from '@testing-library/react';
import { describe, test, expect } from 'vitest';
import StatCards from '../components/StatCards';

describe('StatCards', () => {
  test('affiche un PnL positif avec le signe +', () => {
    render(
      <StatCards
        performance={{ cumulativePnl: 42.5, nTrades: 10, winRate: 0.6, maxDrawdown: -0.05 }}
        status={{ lastZscore: 1.23, isRunning: true }}
      />
    );
    expect(screen.getByText('+42.50')).toBeInTheDocument();
    expect(screen.getByText('60.0%')).toBeInTheDocument();
    expect(screen.getByText('Actif')).toBeInTheDocument();
  });

  test('affiche un PnL négatif sans signe +', () => {
    render(
      <StatCards
        performance={{ cumulativePnl: -12.3, nTrades: 5, winRate: 0.2, maxDrawdown: -0.15 }}
        status={{ lastZscore: -2.1, isRunning: false }}
      />
    );
    expect(screen.getByText('-12.30')).toBeInTheDocument();
    expect(screen.getByText('Arrêté')).toBeInTheDocument();
  });

  test('affiche des tirets quand les données sont absentes', () => {
    render(<StatCards performance={null} status={null} />);
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThan(0);
  });
});
