/**
 * Pokemon Type Badge Component
 * Reusable component for displaying Pokemon types with proper colors
 */
import React from 'react';

interface PokemonTypeBadgeProps {
  type: string;
  className?: string;
  style?: React.CSSProperties;
}

export const PokemonTypeBadge: React.FC<PokemonTypeBadgeProps> = ({ type, className = '', style }) => {
  const normalizedType = type.toLowerCase();
  
  // Get the color for this type from CSS variables
  const getTypeColor = (typeName: string): string => {
    return `var(--color-type-${typeName})`;
  };

  return (
    <span
      className={`badge badge-type type-${normalizedType} ${className}`}
      style={{
        display: 'inline-block',
        padding: '6px 12px',
        backgroundColor: getTypeColor(normalizedType),
        color: 'var(--color-text-white)',
        borderRadius: '6px',
        fontSize: '12px',
        fontWeight: '600',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
        ...style,
      }}
    >
      {type.toUpperCase()}
    </span>
  );
};

