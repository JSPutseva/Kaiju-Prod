import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the Kaiju header', () => {
  render(<App />);
  expect(screen.getByText(/^Kaiju/)).toBeInTheDocument();
});
