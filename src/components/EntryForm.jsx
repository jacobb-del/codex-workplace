import { useState } from 'react';

export default function EntryForm({ onAddEntry }) {
  const [type, setType] = useState('expense');
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));

  function handleSubmit(event) {
    event.preventDefault();
    const parsedAmount = Number(amount);

    if (!description.trim() || !date || Number.isNaN(parsedAmount) || parsedAmount <= 0) {
      return;
    }

    onAddEntry({
      id: crypto.randomUUID(),
      type,
      description: description.trim(),
      amount: parsedAmount,
      date
    });

    setDescription('');
    setAmount('');
  }

  return (
    <form className="entry-form" onSubmit={handleSubmit}>
      <div className="field-row">
        <label>
          Type
          <select value={type} onChange={(event) => setType(event.target.value)}>
            <option value="expense">Expense</option>
            <option value="income">Income</option>
          </select>
        </label>

        <label>
          Date
          <input type="date" value={date} onChange={(event) => setDate(event.target.value)} required />
        </label>

        <label>
          Amount
          <input
            type="number"
            min="0"
            step="0.01"
            placeholder="0.00"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            required
          />
        </label>
      </div>

      <label>
        Description
        <input
          type="text"
          placeholder="e.g. Groceries"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          required
        />
      </label>

      <button type="submit">Add Entry</button>
    </form>
  );
}
