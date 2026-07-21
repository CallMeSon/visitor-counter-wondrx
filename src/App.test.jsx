import { render, screen } from '@testing-library/react';
import App from './App';
import { describe, it, expect } from 'vitest';

describe('App', () => {
  it('renders the initial count', () => {
    render(<App />);
    expect(screen.getByText('0')).toBeInTheDocument();
  });
});
