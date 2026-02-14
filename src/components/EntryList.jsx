function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(value);
}

export default function EntryList({ entries }) {
  if (!entries.length) {
    return <p className="empty-state">No entries for this filter yet.</p>;
  }

  return (
    <ul className="entry-list">
      {entries.map((entry) => (
        <li key={entry.id} className="entry-item">
          <div>
            <p className="entry-description">{entry.description}</p>
            <p className="entry-date">{entry.date}</p>
          </div>
          <span className={entry.type === 'income' ? 'pill income' : 'pill expense'}>
            {entry.type === 'income' ? '+' : '-'} {formatCurrency(entry.amount)}
          </span>
        </li>
      ))}
    </ul>
  );
}
