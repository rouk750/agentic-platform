import { useState, useMemo } from 'react';

export type FilterStatus = 'active' | 'archived' | 'all';
export type SortOption = 'updated_desc' | 'updated_asc' | 'name_asc';

interface SortAndFilterOptions<T> {
  items: T[];
  filterPredicate?: (item: T, status: FilterStatus) => boolean;
  sortComparator?: (a: T, b: T, sortBy: SortOption) => number;
}

export function useSortAndFilter<
  T extends { is_archived?: boolean; updated_at?: string | null; name: string },
>({ items, filterPredicate, sortComparator }: SortAndFilterOptions<T>) {
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('active');
  const [sortBy, setSortBy] = useState<SortOption>('updated_desc');

  const filteredAndSortedItems = useMemo(() => {
    const defaultFilterPredicate = (item: T, status: FilterStatus) => {
      if (status === 'all') return true;
      if (status === 'active') return !item.is_archived;
      if (status === 'archived') return !!item.is_archived;
      return true;
    };

    const defaultSortComparator = (a: T, b: T, sort: SortOption) => {
      if (sort === 'name_asc') return a.name.localeCompare(b.name);
      // Handle potentially missing updated_at by defaulting to 0 (epoch)
      const dateA = new Date(a.updated_at || 0).getTime();
      const dateB = new Date(b.updated_at || 0).getTime();
      return sort === 'updated_desc' ? dateB - dateA : dateA - dateB;
    };

    const predicate = filterPredicate || defaultFilterPredicate;
    const comparator = sortComparator || defaultSortComparator;

    return items
      .filter((item) => predicate(item, filterStatus))
      .sort((a, b) => comparator(a, b, sortBy));
  }, [items, filterStatus, sortBy, filterPredicate, sortComparator]);

  return {
    filterStatus,
    setFilterStatus,
    sortBy,
    setSortBy,
    filteredAndSortedItems,
  };
}
