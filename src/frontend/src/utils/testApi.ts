/**
 * Quick API testing utilities
 * Import this in browser console or use in components for testing
 */

// Example: Test authentication
export const testAuth = async () => {
  const { login, register, getCurrentUser } = await import('../services/authService');
  
  console.log('Testing authentication...');
  
  try {
    // Test register
    const registerResult = await register({
      username: 'testuser' + Date.now(),
      password: 'testpass123'
    });
    console.log('✅ Register success:', registerResult);
    
    // Test get current user
    const user = await getCurrentUser();
    console.log('✅ Get current user success:', user);
    
    return { success: true, user };
  } catch (error) {
    console.error('❌ Auth test failed:', error);
    return { success: false, error };
  }
};

// Example: Test game files
export const testGameFiles = async () => {
  const { createGameFile, getGameFiles } = await import('../services/gameFileService');
  
  console.log('Testing game files...');
  
  try {
    // Create a game file
    const newGameFile = await createGameFile({
      trainer_name: 'Test Trainer',
      game_name: 'black'
    });
    console.log('✅ Create game file success:', newGameFile);
    
    // Get all game files
    const gameFiles = await getGameFiles();
    console.log('✅ Get game files success:', gameFiles);
    
    return { success: true, gameFiles };
  } catch (error) {
    console.error('❌ Game files test failed:', error);
    return { success: false, error };
  }
};

// Example: Test versions (public endpoint, no auth needed)
export const testVersions = async () => {
  const { getVersions, getVersion } = await import('../services/versionService');
  
  console.log('Testing versions (public endpoint)...');
  
  try {
    const versions = await getVersions();
    console.log('✅ Get versions success:', versions);
    
    if (versions.length > 0) {
      const version = await getVersion(versions[0].version_name);
      console.log('✅ Get version success:', version);
    }
    
    return { success: true, versions };
  } catch (error) {
    console.error('❌ Versions test failed:', error);
    return { success: false, error };
  }
};

