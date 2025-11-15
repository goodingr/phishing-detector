import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';

describe('App', () => {
  test('renders phishing analyzer heading', () => {
    render(<App />);
    expect(
      screen.getByRole('heading', { name: /phishing email analyzer/i })
    ).toBeInTheDocument();
  });

  test('enables analyze button after user provides text', async () => {
    render(<App />);

    const analyzeButton = screen.getByRole('button', { name: /analyze email/i });
    expect(analyzeButton).toBeDisabled();

    await userEvent.type(screen.getByLabelText(/subject/i), 'Weekly update');
    expect(analyzeButton).not.toBeDisabled();
  });
});
