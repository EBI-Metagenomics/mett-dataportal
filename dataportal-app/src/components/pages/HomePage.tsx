import React, { useState, useEffect } from 'react';
import { fetchSpeciesList } from '../../services/speciesService';
import { fetchSearchResults } from '../../services/searchService';
import SearchForm from '../organisms/SearchForm';
import ResultsTable from '../organisms/ResultsTable';
import styles from "@components/HomePage/HomePage.module.scss";

const HomePage: React.FC = () => {
  const [results, setResults] = useState<any[]>([]);
  const [speciesList, setSpeciesList] = useState<any[]>([]);
  const [selectedSpecies, setSelectedSpecies] = useState('');
  const [selectedGenome, setSelectedGenome] = useState('');

  // Fetch species list on component mount
  useEffect(() => {
    const fetchSpecies = async () => {
      try {
        const species = await fetchSpeciesList();
        setSpeciesList(species.results || []);
      } catch (error) {
        console.error('Error fetching species:', error);
      }
    };

    fetchSpecies();
  }, []);

  const handleSearch = async () => {
    try {
      const response = await fetchSearchResults(selectedSpecies, selectedGenome);
      setResults(response.results || []);
    } catch (error) {
      console.error('Error fetching search results:', error);
      setResults([]);
    }
  };

  const handleGenomeSelect = (id: string) => {
    setSelectedGenome(id);
  };

  const handleSpeciesChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedSpecies(e.target.value);
  };

  return (
    <div>
      {/* Species Dropdown */}
      <section className="vf-grid vf-grid__col-3">
        <div>
          <label htmlFor="species-select">Select Species:</label>
          <select id="species-select" value={selectedSpecies} onChange={handleSpeciesChange}>
            <option value="">-- Select a Species --</option>
            {speciesList.map(species => (
              <option key={species.id} value={species.id}>
                {species.name}
              </option>
            ))}
          </select>
        </div>
      </section>

      <section className="vf-grid vf-grid__col-3">
        <SearchForm onSearch={handleSearch} />
      </section>

      <section className="vf-grid vf-grid__col-3">
        <ResultsTable results={results} onGenomeSelect={handleGenomeSelect} selectedGenome={selectedGenome} />
      </section>
    </div>
  );
};

export default HomePage;
