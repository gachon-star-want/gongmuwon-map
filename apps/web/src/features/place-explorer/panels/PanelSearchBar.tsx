import { ActionIcon, TextInput } from '@mantine/core';
import { Search, X } from 'lucide-react';

interface PanelSearchBarProps {
  value: string;
  onChange: (value: string) => void;
}

export function PanelSearchBar({ value, onChange }: PanelSearchBarProps) {
  return (
    <div className="panel-search-wrap">
      <TextInput
        className="panel-search"
        leftSection={<Search size={16} />}
        placeholder="식당명, 자치구, 부서 검색"
        value={value}
        onChange={(event) => onChange(event.currentTarget.value)}
        rightSection={
          value ? (
            <ActionIcon variant="subtle" aria-label="검색 지우기" onClick={() => onChange('')}>
              <X size={14} />
            </ActionIcon>
          ) : null
        }
      />
    </div>
  );
}
