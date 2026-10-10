import React, { createContext, useContext, useState, useEffect } from 'react';
import { BrandProfile } from '../types';
import { brandService } from '../services/api';
import { useAuth } from './AuthContext';

interface BrandContextType {
  brands: BrandProfile[];
  currentBrand: BrandProfile | null;
  setCurrentBrand: (brand: BrandProfile) => void;
  selectBrandById: (brandId: string) => void;
  isLoading: boolean;
  refreshBrands: () => Promise<void>;
}

const BrandContext = createContext<BrandContextType | undefined>(undefined);

export const BrandProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [brands, setBrands] = useState<BrandProfile[]>([]);
  const [currentBrand, setCurrentBrand] = useState<BrandProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchBrands = async () => {
    setIsLoading(true);
    try {
      const allBrands = await brandService.getAllBrands();
      const cleanBrands = Array.from(
        new Map(allBrands.map(b => [b.name.toLowerCase().trim(), b])).values()
      ).filter(b => b.name.toLowerCase().trim() !== 'nova commerce');
      setBrands(cleanBrands);
      
      // Select brand based on user association or first
      if (user?.associatedBrandId) {
        const found = cleanBrands.find(b => b.id === user.associatedBrandId);
        setCurrentBrand(found || cleanBrands[0] || null);
      } else if (cleanBrands.length > 0 && !currentBrand) {
        setCurrentBrand(cleanBrands[0]);
      }
    } catch (err) {
      console.error('Failed to load brands', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBrands();
  }, [user]);

  const selectBrandById = (brandId: string) => {
    const found = brands.find(b => b.id === brandId);
    if (found) {
      setCurrentBrand(found);
    }
  };

  return (
    <BrandContext.Provider
      value={{
        brands,
        currentBrand,
        setCurrentBrand,
        selectBrandById,
        isLoading,
        refreshBrands: fetchBrands
      }}
    >
      {children}
    </BrandContext.Provider>
  );
};

export const useBrand = () => {
  const context = useContext(BrandContext);
  if (!context) {
    throw new Error('useBrand must be used within a BrandProvider');
  }
  return context;
};
