function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(value);
}

export default function SummaryCard({ income, expenses, balance }) {
  return (
    <section className="summary-grid" aria-label="Financial summary">
      <article>
        <h2>Total Balance</h2>
        <p className={balance >= 0 ? 'value positive' : 'value negative'}>{formatCurrency(balance)}</p>
      </article>
      <article>
        <h3>Income</h3>
        <p className="value positive">{formatCurrency(income)}</p>
      </article>
      <article>
        <h3>Expenses</h3>
        <p className="value negative">{formatCurrency(expenses)}</p>
      </article>
    </section>
  );
}
