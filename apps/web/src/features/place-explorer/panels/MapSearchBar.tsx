import { ActionIcon, TextInput } from '@mantine/core';
import { Search, X } from 'lucide-react';

interface MapSearchBarProps {
  value: string;
  onChange: (value: string) => void;
}

export function MapSearchBar({ value, onChange }: MapSearchBarProps) {
  return (
    <div className="map-search-bar">
      <TextInput
        leftSection={<Search size={18} />}
        placeholder="식당명, 자치구, 부서 검색"
        value={value}
        onChange={(event) => onChange(event.currentTarget.value)}
        rightSection={
          value ? (
            <ActionIcon variant="subtle" aria-label="검색 지우기" onClick={() => onChange('')}>
              <X size={16} />
            </ActionIcon>
          ) : null
        }
      />
    </div>
  );
}
