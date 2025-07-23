import React, { useState } from "react";
import axios from "axios";
import styles from "./NaturalQueryBox.module.scss";

interface NaturalQueryBoxProps {
  onQueryResult: (filters: Record<string, unknown>) => void;
}

const NaturalQueryBox = ({ onQueryResult }: NaturalQueryBoxProps) => {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      // Send query as URL parameter, not in request body
      const encodedQuery = encodeURIComponent(input);
      const response = await axios.post(`/api/query/interpret?query=${encodedQuery}`);
      onQueryResult(response.data);  // This could trigger your gene search
    } catch (err) {
      console.error(err);
      alert("Failed to interpret query.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.formSection}>
      <label className={styles.label}>Ask a question</label>
      <div className={styles.sequenceInputBox}>
        <textarea
          className={styles.textarea}
          value={input}
          placeholder="Ask something like: essential genes in BU involved in AMR"
          onChange={(e) => setInput(e.target.value)}
          rows={6}
        />
      </div>
      <div className={styles.buttonRow}>
        <button
          onClick={handleSubmit}
          disabled={loading}
          className={styles.vfButton}
        >
          {loading ? "Interpreting..." : "Ask"}
        </button>
      </div>
    </div>
  );
};

export default NaturalQueryBox;