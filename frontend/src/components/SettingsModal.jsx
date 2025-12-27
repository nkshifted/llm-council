import { useState, useEffect } from 'react';
import { api } from '../api';
import './SettingsModal.css';

export default function SettingsModal({ isOpen, onClose, config, onConfigSaved }) {
  const [localConfig, setLocalConfig] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const [isDirty, setIsDirty] = useState(false);
  const [testResults, setTestResults] = useState({});
  const [testingId, setTestingId] = useState(null);
  const [saveError, setSaveError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  // Initialize local config when modal opens
  useEffect(() => {
    if (isOpen && config) {
      setLocalConfig(JSON.parse(JSON.stringify(config)));
      setIsDirty(false);
      setTestResults({});
      setSaveError(null);
    }
  }, [isOpen, config]);

  if (!isOpen || !localConfig) return null;

  const enabledClis = localConfig.clis.filter((cli) => cli.enabled);
  const isChairman = (cliId) => localConfig.chairman_id === cliId;
  const isLastCli = localConfig.clis.length === 1;
  const isLastEnabled = enabledClis.length === 1;

  const handleClose = () => {
    if (isDirty) {
      if (!window.confirm('You have unsaved changes. Discard them?')) {
        return;
      }
    }
    onClose();
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      handleClose();
    }
  };

  const updateCli = (cliId, field, value) => {
    setLocalConfig((prev) => ({
      ...prev,
      clis: prev.clis.map((cli) =>
        cli.id === cliId ? { ...cli, [field]: value } : cli
      ),
    }));
    setIsDirty(true);
  };

  const handleArgsChange = (cliId, argsString) => {
    // Split by spaces, but handle empty string
    const args = argsString.trim() ? argsString.trim().split(/\s+/) : [];
    updateCli(cliId, 'args', args);
  };

  const handleToggleEnabled = (cliId) => {
    const cli = localConfig.clis.find((c) => c.id === cliId);
    if (!cli) return;

    // Can't disable chairman
    if (isChairman(cliId) && cli.enabled) {
      alert('Cannot disable the chairman. Select a different chairman first.');
      return;
    }

    // Can't disable last enabled CLI
    if (isLastEnabled && cli.enabled) {
      alert('At least one CLI must be enabled.');
      return;
    }

    updateCli(cliId, 'enabled', !cli.enabled);
  };

  const handleDelete = (cliId) => {
    if (isChairman(cliId)) {
      alert('Cannot delete the chairman. Select a different chairman first.');
      return;
    }
    if (isLastCli) {
      alert('Cannot delete the last CLI.');
      return;
    }

    if (!window.confirm('Delete this CLI configuration?')) {
      return;
    }

    setLocalConfig((prev) => ({
      ...prev,
      clis: prev.clis.filter((cli) => cli.id !== cliId),
      council_ids: prev.council_ids.filter((id) => id !== cliId),
    }));
    setIsDirty(true);

    if (expandedId === cliId) {
      setExpandedId(null);
    }
  };

  const handleAddCli = () => {
    const newId = `cli_${Date.now()}`;
    const newCli = {
      id: newId,
      name: 'New CLI',
      command: '',
      args: [],
      enabled: true,
    };

    setLocalConfig((prev) => ({
      ...prev,
      clis: [...prev.clis, newCli],
      council_ids: [...prev.council_ids, newId],
    }));
    setExpandedId(newId);
    setIsDirty(true);
  };

  const handleChairmanChange = (newChairmanId) => {
    setLocalConfig((prev) => ({
      ...prev,
      chairman_id: newChairmanId,
    }));
    setIsDirty(true);
  };

  const handleTest = async (cli) => {
    setTestingId(cli.id);
    setTestResults((prev) => ({ ...prev, [cli.id]: null }));

    try {
      const result = await api.testCli(cli.command, cli.args);
      setTestResults((prev) => ({ ...prev, [cli.id]: result }));
    } catch (error) {
      setTestResults((prev) => ({
        ...prev,
        [cli.id]: { success: false, error: error.message },
      }));
    } finally {
      setTestingId(null);
    }
  };

  const handleSave = async () => {
    setSaveError(null);
    setIsSaving(true);

    try {
      await api.saveConfig(localConfig);
      setIsDirty(false);
      onConfigSaved(localConfig);
      onClose();
    } catch (error) {
      setSaveError(error.message);
    } finally {
      setIsSaving(false);
    }
  };

  const toggleExpanded = (cliId) => {
    setExpandedId(expandedId === cliId ? null : cliId);
  };

  return (
    <div className="settings-modal-backdrop" onClick={handleBackdropClick}>
      <div className="settings-modal">
        <div className="settings-modal-header">
          <h2>Settings</h2>
          <button className="close-btn" onClick={handleClose}>
            &times;
          </button>
        </div>

        <div className="settings-modal-content">
          <div className="settings-section">
            <h3>CLI Configurations</h3>
            <div className="cli-list">
              {localConfig.clis.map((cli) => (
                <div key={cli.id} className="cli-item">
                  <div
                    className="cli-header"
                    onClick={() => toggleExpanded(cli.id)}
                  >
                    <span className={`expand-arrow ${expandedId === cli.id ? 'expanded' : ''}`}>
                      &#9654;
                    </span>
                    <span className="cli-name">
                      {cli.name}
                      {isChairman(cli.id) && (
                        <span className="chairman-badge">Chairman</span>
                      )}
                    </span>
                    <label
                      className="toggle-switch"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        type="checkbox"
                        checked={cli.enabled}
                        onChange={() => handleToggleEnabled(cli.id)}
                        disabled={isChairman(cli.id) && cli.enabled}
                      />
                      <span className="toggle-slider"></span>
                    </label>
                  </div>

                  {expandedId === cli.id && (
                    <div className="cli-details">
                      <div className="form-group">
                        <label>Name</label>
                        <input
                          type="text"
                          value={cli.name}
                          onChange={(e) =>
                            updateCli(cli.id, 'name', e.target.value)
                          }
                          placeholder="Display name"
                        />
                      </div>

                      <div className="form-group">
                        <label>Command</label>
                        <input
                          type="text"
                          value={cli.command}
                          onChange={(e) =>
                            updateCli(cli.id, 'command', e.target.value)
                          }
                          placeholder="e.g., gemini"
                        />
                      </div>

                      <div className="form-group">
                        <label>Arguments (space-separated)</label>
                        <input
                          type="text"
                          value={cli.args.join(' ')}
                          onChange={(e) =>
                            handleArgsChange(cli.id, e.target.value)
                          }
                          placeholder="e.g., -p or exec"
                        />
                      </div>

                      <div className="cli-actions">
                        <button
                          className="test-btn"
                          onClick={() => handleTest(cli)}
                          disabled={!cli.command || testingId === cli.id}
                        >
                          {testingId === cli.id ? 'Testing...' : 'Test'}
                        </button>
                        <button
                          className="delete-btn"
                          onClick={() => handleDelete(cli.id)}
                          disabled={isChairman(cli.id) || isLastCli}
                        >
                          Delete
                        </button>
                      </div>

                      {testResults[cli.id] && (
                        <div
                          className={`test-result ${
                            testResults[cli.id].success ? 'success' : 'error'
                          }`}
                        >
                          {testResults[cli.id].success ? (
                            <>
                              <span className="test-icon">&#10003;</span>
                              <span className="test-message">
                                {testResults[cli.id].response}
                              </span>
                            </>
                          ) : (
                            <>
                              <span className="test-icon">&#10007;</span>
                              <span className="test-message">
                                {testResults[cli.id].error}
                              </span>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <button className="add-cli-btn" onClick={handleAddCli}>
              + Add CLI
            </button>
          </div>

          <div className="settings-section">
            <h3>Chairman</h3>
            <p className="section-description">
              The chairman synthesizes the final response from all council members.
            </p>
            <select
              value={localConfig.chairman_id}
              onChange={(e) => handleChairmanChange(e.target.value)}
              className="chairman-select"
            >
              {enabledClis.map((cli) => (
                <option key={cli.id} value={cli.id}>
                  {cli.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {saveError && <div className="save-error">{saveError}</div>}

        <div className="settings-modal-footer">
          <button className="cancel-btn" onClick={handleClose}>
            Cancel
          </button>
          <button
            className="save-btn"
            onClick={handleSave}
            disabled={isSaving || !isDirty}
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
