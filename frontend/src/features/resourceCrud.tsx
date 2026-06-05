import { Pencil, Plus, RefreshCw, Trash2, X } from "lucide-react";
import { useCallback, useEffect, useState, type FormEvent } from "react";

import { ApiClientError, useApiClient } from "../shared/api";
import { Button, Panel, StatusBadge } from "../shared/ui";

export type ResourceFieldType = "string" | "text" | "int" | "float" | "bool" | "datetime" | "date" | "uuid" | "enum";

export interface ResourceField {
  enumValues?: string[];
  label: string;
  name: string;
  optional: boolean;
  type: ResourceFieldType;
}

export interface ResourceCrudConfig {
  endpoint: string;
  fields: ResourceField[];
  name: string;
  title: string;
}

type ResourceRecord = Record<string, unknown> & {
  id: string;
};

export function ResourceCrudPage({ config }: { config: ResourceCrudConfig }) {
  const apiClient = useApiClient();
  const [editingItem, setEditingItem] = useState<ResourceRecord | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string | boolean>>(() => initialFormValues(config.fields));
  const [items, setItems] = useState<ResourceRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadItems = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.get<ResourceRecord[]>(config.endpoint);
      setItems(result.data);
    } catch (loadError) {
      setError(messageForError(loadError));
    } finally {
      setLoading(false);
    }
  }, [apiClient, config.endpoint]);

  useEffect(() => {
    void loadItems();
  }, [loadItems]);

  async function saveItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = payloadFromValues(formValues, config.fields);
    setError(null);
    try {
      if (editingItem) {
        await apiClient.patch(`${config.endpoint}/${editingItem.id}`, payload);
      } else {
        await apiClient.post(config.endpoint, payload);
      }
      resetForm();
      await loadItems();
    } catch (saveError) {
      setError(messageForError(saveError));
    }
  }

  async function deleteItem(itemId: string) {
    setError(null);
    try {
      await apiClient.delete(`${config.endpoint}/${itemId}`);
      await loadItems();
    } catch (deleteError) {
      setError(messageForError(deleteError));
    }
  }

  return (
    <div className="resource-page">
      <Panel
        actions={
          <Button icon={<RefreshCw size={16} />} onClick={() => void loadItems()} variant="ghost">
            Refresh
          </Button>
        }
        title={config.title}
      >
        <form className="resource-form" onSubmit={(event) => void saveItem(event)}>
          {config.fields.map((field) => (
            <FieldInput
              field={field}
              key={field.name}
              onChange={(value) => setFieldValue(field.name, value)}
              value={formValues[field.name] ?? ""}
            />
          ))}
          <Button icon={editingItem ? <Pencil size={16} /> : <Plus size={16} />} type="submit">
            {editingItem ? "Update" : "Create"}
          </Button>
          {editingItem ? (
            <Button icon={<X size={16} />} onClick={resetForm} variant="ghost">
              Cancel
            </Button>
          ) : null}
        </form>
        {error ? <p className="error-message">{error}</p> : null}
        <ResourceTable config={config} items={items} loading={loading} onDelete={deleteItem} onEdit={editItem} />
      </Panel>
    </div>
  );

  function editItem(item: ResourceRecord) {
    setEditingItem(item);
    setFormValues(valuesFromRecord(item, config.fields));
  }

  function resetForm() {
    setEditingItem(null);
    setFormValues(initialFormValues(config.fields));
  }

  function setFieldValue(name: string, value: string | boolean) {
    setFormValues((current) => ({ ...current, [name]: value }));
  }
}

function FieldInput({
  field,
  onChange,
  value,
}: {
  field: ResourceField;
  onChange: (value: string | boolean) => void;
  value: string | boolean;
}) {
  if (field.type === "bool") {
    return (
      <label className="checkbox-field">
        <input checked={Boolean(value)} name={field.name} onChange={(event) => onChange(event.target.checked)} type="checkbox" />
        <span>{field.label}</span>
      </label>
    );
  }

  if (field.type === "enum") {
    return (
      <label className="form-field">
        <span>{field.label}</span>
        <select name={field.name} onChange={(event) => onChange(event.target.value)} required={!field.optional} value={String(value)}>
          <option value="">Select</option>
          {(field.enumValues || []).map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </label>
    );
  }

  return (
    <label className="form-field">
      <span>{field.label}</span>
      <input
        name={field.name}
        onChange={(event) => onChange(event.target.value)}
        required={!field.optional}
        type={inputTypeFor(field.type)}
        value={String(value)}
      />
    </label>
  );
}

function ResourceTable({
  config,
  items,
  loading,
  onDelete,
  onEdit,
}: {
  config: ResourceCrudConfig;
  items: ResourceRecord[];
  loading: boolean;
  onDelete: (itemId: string) => Promise<void>;
  onEdit: (item: ResourceRecord) => void;
}) {
  if (loading) {
    return <StatusBadge tone="neutral">Loading</StatusBadge>;
  }

  if (items.length === 0) {
    return <p className="empty-state">No records</p>;
  }

  return (
    <div className="table-wrap">
      <table className="resource-table">
        <thead>
          <tr>
            <th>ID</th>
            {config.fields.map((field) => (
              <th key={field.name}>{field.label}</th>
            ))}
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.id}</td>
              {config.fields.map((field) => (
                <td key={field.name}>{formatValue(item[field.name])}</td>
              ))}
              <td>
                <Button icon={<Pencil size={16} />} onClick={() => onEdit(item)} variant="ghost">
                  Edit
                </Button>
                <Button icon={<Trash2 size={16} />} onClick={() => void onDelete(item.id)} variant="ghost">
                  Delete
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function payloadFromValues(values: Record<string, string | boolean>, fields: ResourceField[]): Record<string, unknown> {
  return Object.fromEntries(
    fields.flatMap((field) => {
      const value = values[field.name];
      if (field.type === "bool") {
        return [[field.name, Boolean(value)]];
      }
      if ((value === undefined || value === "") && field.optional) {
        return [];
      }
      return [[field.name, coerceValue(value, field)]];
    }),
  );
}

function coerceValue(value: string | boolean | undefined, field: ResourceField): unknown {
  if (value === undefined) {
    return null;
  }
  const text = String(value);
  if (field.type === "int") {
    return Number.parseInt(text, 10);
  }
  if (field.type === "float") {
    return Number.parseFloat(text);
  }
  return text;
}

function initialFormValues(fields: ResourceField[]): Record<string, string | boolean> {
  return Object.fromEntries(fields.map((field) => [field.name, field.type === "bool" ? false : ""]));
}

function valuesFromRecord(record: ResourceRecord, fields: ResourceField[]): Record<string, string | boolean> {
  return Object.fromEntries(
    fields.map((field) => {
      const value = record[field.name];
      return [field.name, field.type === "bool" ? Boolean(value) : formatValue(value)];
    }),
  );
}

function inputTypeFor(type: ResourceFieldType): string {
  if (type === "datetime") {
    return "datetime-local";
  }
  if (type === "date") {
    return "date";
  }
  if (type === "int" || type === "float") {
    return "number";
  }
  return "text";
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "bigint") {
    return value.toString();
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return "";
}

function messageForError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return `${error.code}: ${error.message}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected error";
}
